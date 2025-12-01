#!/bin/bash
# Convert PNG/JPG images to WebP format for better performance
# Requires: brew install webp

echo "🖼️  Image Optimization Script"
echo "================================"
echo ""

# Check if cwebp is installed
if ! command -v cwebp &> /dev/null; then
    echo "❌ cwebp not found. Installing via Homebrew..."
    brew install webp
fi

# Find all PNG and JPG images in content and static directories
find content static -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | while read -r img; do
    # Skip if WebP already exists
    webp_file="${img%.*}.webp"
    
    if [ -f "$webp_file" ]; then
        echo "⏭️  Skipping (WebP exists): $img"
        continue
    fi
    
    # Get original size
    orig_size=$(du -h "$img" | cut -f1)
    
    # Convert to WebP with quality 85 (good balance of quality/size)
    cwebp -q 85 "$img" -o "$webp_file" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        webp_size=$(du -h "$webp_file" | cut -f1)
        echo "✅ Converted: $img ($orig_size → $webp_size)"
    else
        echo "❌ Failed: $img"
    fi
done

echo ""
echo "================================"
echo "✅ Image optimization complete!"
echo ""
echo "Next steps:"
echo "1. Hugo will automatically serve WebP to modern browsers"
echo "2. PNG files are kept as fallbacks for older browsers"
echo "3. Rebuild your Hugo site to see the improvements"
