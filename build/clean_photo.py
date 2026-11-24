# Photo cleanup for the gallery: even out shadows, bring back detail in bright areas, fix color casts.
# Gentle on purpose: label colors must stay true.
import cv2, numpy as np
from PIL import Image

def clean(im: Image.Image, shadow=0.35, clahe=1.25) -> Image.Image:
    rgb = np.asarray(im.convert('RGB')).astype(np.float32)
    # 1) White balance from neutral, bright pixels only (white paper, bare aluminum), never from the label colors.
    hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV)
    neutral = (hsv[..., 1] < 40) & (hsv[..., 2] > 150) & (hsv[..., 2] < 250)
    if neutral.mean() > 0.05:
        m = rgb[neutral].mean(0)
        gain = np.clip(m.mean() / np.maximum(m, 1), 0.85, 1.15)
        rgb = np.clip(rgb * gain, 0, 255)
    lab = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2LAB)
    L = lab[..., 0].astype(np.float32)
    # 2) Shadows: lighting estimated with a very wide blur, partly divided out (wide = no halos around labels).
    small = cv2.resize(L, (64, 64), interpolation=cv2.INTER_AREA)
    light = cv2.resize(cv2.GaussianBlur(small, (0, 0), 12), (L.shape[1], L.shape[0]), interpolation=cv2.INTER_CUBIC) + 1
    L = L * (light.mean() / light) ** shadow
    # 3) Gentle levels stretch (0.5% - 99.7%), then mild local contrast for washed-out text.
    lo, hi = np.percentile(L, (0.5, 99.7))
    if hi - lo > 40: L = (L - lo) / (hi - lo) * 250 + 3
    L = cv2.createCLAHE(clipLimit=clahe, tileGridSize=(6, 6)).apply(np.clip(L, 0, 255).astype(np.uint8))
    lab[..., 0] = L
    return Image.fromarray(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB))


def whiten_background(im: Image.Image, tol=7, feather=3) -> Image.Image:
    """Turn the paper/backdrop around a label pure white (removes cast shadows on the paper).
    Only used when the border of the photo is light and plain."""
    rgb = np.asarray(im.convert('RGB'))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, w = rgb.shape[:2]
    border = np.concatenate([hsv[0], hsv[-1], hsv[:, 0], hsv[:, -1]])
    if np.median(border[:, 2]) < 150 or np.median(border[:, 1]) > 45:
        return im  # dark or colorful backdrop: leave alone
    g = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), (5, 5), 0)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    # Edges act as a wall: the fill cannot cross the outline of the label into silver or white parts.
    edges = cv2.dilate(cv2.Canny(g, 18, 50), np.ones((5, 5), np.uint8))
    mask[1:-1, 1:-1][edges > 0] = 1
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    for x in range(0, w, max(1, w // 40)):
        for y in (0, h - 1):
            if mask[y + 1, x + 1] == 0 and hsv[y, x, 2] > 120 and hsv[y, x, 1] < 60:
                cv2.floodFill(g, mask, (x, y), 0, tol, tol, flags)
    for y in range(0, h, max(1, h // 40)):
        for x in (0, w - 1):
            if mask[y + 1, x + 1] == 0 and hsv[y, x, 2] > 120 and hsv[y, x, 1] < 60:
                cv2.floodFill(g, mask, (x, y), 0, tol, tol, flags)
    bg = (mask[1:-1, 1:-1] == 255).astype(np.uint8)
    # Close the thin edge band next to the background too, so no gray ring is left.
    bg = cv2.morphologyEx(bg, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    # Keep only big solid objects (the labels), with everything inside their outline protected.
    fg = (1 - bg).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    big = [k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] >= 0.03 * h * w]
    if not big or max(stats[k, cv2.CC_STAT_AREA] for k in big) < 0.15 * h * w:
        return im  # no clear label shape (label fills the photo, or a busy scene): leave alone
    keep = np.isin(lab, big).astype(np.uint8)
    cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    solid = np.zeros_like(keep); cv2.drawContours(solid, cnts, -1, 1, thickness=cv2.FILLED)
    # A real label is a compact shape; a ragged outline means the fill leaked into it.
    for c in cnts:
        if cv2.contourArea(c) >= 0.03 * h * w and cv2.contourArea(c) / max(cv2.contourArea(cv2.convexHull(c)), 1) < 0.85:
            return im
    bg = 1 - solid
    m = bg.astype(np.float32)
    if m.mean() > 0.85 or m.mean() < 0.03:
        return im  # filled (almost) everything or nothing: not a label-on-paper photo
    m = cv2.erode(m, np.ones((3, 3), np.uint8))
    m = cv2.GaussianBlur(m, (0, 0), feather)[..., None]
    out = rgb * (1 - m) + 250 * m
    return Image.fromarray(out.astype(np.uint8))


def even_silver(im: Image.Image, strength=0.9) -> Image.Image:
    """Even out lighting across silver/white surfaces (dark top and bottom of a metallic label).
    The lighting is measured on light, colorless pixels only, so ink and paint don't skew it;
    every pixel is then scaled by the same local factor, so dark ink stays dark."""
    rgb = np.asarray(im.convert('RGB')).astype(np.float32)
    lab = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2LAB)
    L = lab[..., 0].astype(np.float32)
    hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV)
    h, w = L.shape
    # "Surface" pixels: colorless and not ink-dark.
    m = ((hsv[..., 1] < 45) & (L > 0.45 * np.percentile(L, 95))).astype(np.float32)
    sig = max(h, w) / 14
    num = cv2.GaussianBlur(L * m, (0, 0), sig); den = cv2.GaussianBlur(m, (0, 0), sig)
    light = num / np.maximum(den, 1e-3)
    target = np.percentile(L[m > 0], 75) if m.sum() > 100 else L.mean()
    gain = (target / np.maximum(light, 1)) ** strength
    conf = np.clip(den / 0.25, 0, 1)            # little surface nearby: correct less
    gain = 1 + (np.clip(gain, 0.7, 1.8) - 1) * conf
    lab[..., 0] = np.clip(L * gain, 0, 255).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB))


def crop_to_subject(im: Image.Image, pad=0.04) -> Image.Image:
    """Crop away plain paper/backdrop around the label: keep the area that has detail (edges, lettering)."""
    small = im.convert('L'); small.thumbnail((500, 500))
    g = cv2.GaussianBlur(np.asarray(small), (5, 5), 0)
    e = cv2.Canny(g, 40, 120)
    e = cv2.morphologyEx(e, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats((e > 0).astype(np.uint8), 8)
    sh, sw = g.shape
    keep = [k for k in range(1, n) if st[k, cv2.CC_STAT_AREA] > 0.002 * sh * sw]  # ignore specks of paper texture
    if not keep: return im
    xs = [st[k, 0] for k in keep]; ys = [st[k, 1] for k in keep]
    xe = [st[k, 0] + st[k, 2] for k in keep]; ye = [st[k, 1] + st[k, 3] for k in keep]
    l, t, r, b = min(xs), min(ys), max(xe), max(ye)
    if (r - l) * (b - t) > 0.85 * sh * sw: return im  # subject already fills the photo
    p = int(pad * max(r - l, b - t))
    l, t, r, b = max(0, l - p), max(0, t - p), min(sw, r + p), min(sh, b + p)
    fx, fy = im.width / sw, im.height / sh
    return im.crop((int(l * fx), int(t * fy), int(r * fx), int(b * fy)))
