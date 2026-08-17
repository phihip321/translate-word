import yaml
import os

config_path = "config/config.yaml"
print("=" * 60)
print("🔍 KIỂM TRA CẤU HÌNH")
print("=" * 60)

if not os.path.exists(config_path):
    print(f"❌ Không tìm thấy: {config_path}")
else:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ File cấu hình: {config_path}")
    print(f"  - PDF method: {config['pdf']['method']}")
    print(f"  - API Key: {'✅ Có' if config['translation']['api_key'] else '❌ CHƯA CÓ'}")
    print(f"  - Model: {config['translation']['model']}")
    print(f"  - Batch size: {config['translation']['batch_size']}")
    
    if not config['translation']['api_key']:
        print("\n⚠️ VUI LÒNG THÊM API KEY VÀO config/config.yaml")
