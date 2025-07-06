#!/usr/bin/env python3
"""
Script to download OmniParser model weights from HuggingFace
"""
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download

def download_omniparser_models():
    """Download OmniParser V2 model weights"""
    print("Downloading OmniParser V2 models...")
    
    # Create weights directory
    weights_dir = Path(__file__).parent.parent / "weights"
    weights_dir.mkdir(exist_ok=True)
    
    try:
        # Download OmniParser V2 models
        snapshot_download(
            repo_id="microsoft/OmniParser-v2.0",
            local_dir=str(weights_dir),
            allow_patterns=[
                "icon_detect/train_args.yaml",
                "icon_detect/model.pt",
                "icon_detect/model.yaml",
                "icon_caption/config.json",
                "icon_caption/generation_config.json",
                "icon_caption/model.safetensors",
                "icon_caption/preprocessor_config.json",
                "icon_caption/tokenizer.json",
                "icon_caption/tokenizer_config.json"
            ]
        )
        
        # Rename icon_caption to icon_caption_florence
        icon_caption_dir = weights_dir / "icon_caption"
        icon_caption_florence_dir = weights_dir / "icon_caption_florence"
        
        if icon_caption_dir.exists() and not icon_caption_florence_dir.exists():
            icon_caption_dir.rename(icon_caption_florence_dir)
        
        print("✓ Successfully downloaded OmniParser V2 models")
        print(f"  Models saved to: {weights_dir}")
        
    except Exception as e:
        print(f"✗ Error downloading models: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_omniparser_models()