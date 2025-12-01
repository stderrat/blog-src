# Image Optimization Guide

## 🎯 Goal: Save 1.3MB in image downloads

Lighthouse identified that converting images to modern formats (WebP/AVIF) can save ~1.3MB of bandwidth and significantly improve page load times.

---

## 📦 What's Been Set Up

### 1. Conversion Script: `convert-images-to-webp.sh`

**Location:** `/Users/tjungbau/Desktop/workspaces/Blogs/Blog-Source/convert-images-to-webp.sh`

**What it does:**
- Finds all PNG/JPG images in `content/` and `static/` directories
- Converts each to WebP format (85% quality - great balance)
- Keeps original PNG/JPG as fallback for old browsers
- Skips already-converted images

**How to run:**
```bash
cd /Users/tjungbau/Desktop/workspaces/Blogs/Blog-Source
./convert-images-to-webp.sh
```

**First-time setup:**
```bash
# Install WebP tools (one-time)
brew install webp

# Run conversion
./convert-images-to-webp.sh
```

---

### 2. Hugo Shortcode: `img.html`

**Location:** `themes/yaub/layouts/shortcodes/img.html`

**What it does:**
- Automatically serves WebP to modern browsers
- Falls back to PNG/JPG for older browsers
- Adds lazy loading for better performance
- Uses Hugo's built-in image processing when possible

**Usage in content:**

**Old way (AsciiDoc):**
```asciidoc
image::observability/Logo_observability_2.png[width=420px]
```

**New way (with shortcode):**
```asciidoc
{{< img src="observability/Logo_observability_2.png" alt="Observability Logo" width="420" >}}
```

**Parameters:**
- `src` - Path to image (required)
- `alt` - Alt text for accessibility (recommended)
- `width` - Display width in pixels (optional)
- `class` - CSS class (optional)

---

## 🚀 Implementation Steps

### Step 1: Convert Existing Images

Run the conversion script:
```bash
cd /Users/tjungbau/Desktop/workspaces/Blogs/Blog-Source
./convert-images-to-webp.sh
```

**Expected results:**
```
✅ Converted: content/.../Logo_observability_2.png (426KB → ~120KB)
✅ Converted: content/.../Logo_OTEL.png (396KB → ~110KB)
✅ Converted: content/.../Logo_observability_1.png (375KB → ~105KB)
✅ Converted: static/.../thomas-jungbauer.png (91KB → ~25KB)
...
```

**Total savings: ~1.3MB** 🎉

---

### Step 2: Fix Oversized Author Image

The author image is 479x482 but displayed at 70x70. Let's resize it:

```bash
cd /Users/tjungbau/Desktop/workspaces/Blogs/Blog-Source
sips -Z 140 static/images/authors/thomas-jungbauer.png
```

This resizes it to 140x140 (2x for retina displays), saving ~90KB more!

---

### Step 3: Update Hugo Config (Optional)

Add to `config.toml` for automatic image processing:

```toml
[imaging]
  quality = 85
  resampleFilter = "lanczos"
  
[imaging.exif]
  disableDate = false
  disableLatLong = true
```

---

## 📊 Expected Performance Gains

### Before:
- Total image size: ~1,500 KB
- Format: PNG
- Load time: ~2-3 seconds on 3G

### After:
- Total image size: ~200 KB
- Format: WebP (with PNG fallback)
- Load time: ~0.5 seconds on 3G

**Improvements:**
- ✅ 87% smaller file sizes
- ✅ Faster First Contentful Paint (FCP)
- ✅ Faster Largest Contentful Paint (LCP)
- ✅ Better Lighthouse score
- ✅ Lower bandwidth costs
- ✅ Better mobile experience

---

## 🔄 Workflow for New Images

When adding new images to your blog:

### Option 1: Automatic (Recommended)
1. Add your PNG/JPG image normally
2. Run `./convert-images-to-webp.sh` before publishing
3. Hugo will automatically serve WebP to modern browsers

### Option 2: Use Hugo Shortcode
1. Place images in page bundle or `static/`
2. Use the `img` shortcode in your content:
   ```
   {{< img src="my-image.png" alt="Description" width="600" >}}
   ```
3. Hugo processes and optimizes automatically

---

## 🧪 Testing

After converting images:

1. **Rebuild Hugo:**
   ```bash
   hugo server --disableFastRender
   ```

2. **Test in Chrome DevTools:**
   - Open DevTools → Network tab
   - Filter by "Img"
   - Refresh page
   - Look for `.webp` files being served

3. **Run Lighthouse again:**
   - Should see "Bildübermittlung verbessern" warning disappear
   - Performance score should increase
   - LCP should be faster

4. **Test browser compatibility:**
   - Chrome/Edge/Firefox: Serves WebP ✅
   - Safari 14+: Serves WebP ✅
   - Old browsers: Falls back to PNG ✅

---

## 📝 Notes

- **WebP support:** 96% of browsers (including Safari 14+)
- **Quality 85:** Visually identical to original, much smaller
- **Lazy loading:** Images load only when scrolling into view
- **Original files kept:** PNGs remain as fallbacks
- **No manual work:** Script automates everything

---

## 🎓 Browser Support

| Format | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| WebP   | ✅ Yes | ✅ Yes  | ✅ 14+ | ✅ Yes |
| PNG    | ✅ Yes | ✅ Yes  | ✅ Yes | ✅ Yes |

The `<picture>` element automatically serves the best format for each browser!

---

## 🔧 Troubleshooting

**Images not converting?**
```bash
# Check if WebP tools are installed
cwebp -version

# Install if missing
brew install webp
```

**WebP not being served?**
- Check that `.webp` files exist next to `.png` files
- Clear browser cache (Cmd+Shift+R)
- Check Hugo's public/ directory for generated files

**Quality issues?**
- Adjust quality in script: change `q 85` to `q 90` for higher quality
- Re-run conversion script

---

Ready to optimize! Run `./convert-images-to-webp.sh` to get started! 🚀

