"""
诊断脚本：检查 Token 解码问题
"""
import os
import sys
from app.config import settings
from app.utils.security import decode_access_token

def main():
    """主函数"""
    print("=" * 60)
    print("Token 解码诊断工具")
    print("=" * 60)
    print(f"\n当前配置:")
    print(f"  SECRET_KEY: {settings.SECRET_KEY[:20]}... (长度: {len(settings.SECRET_KEY)})")
    print(f"  ALGORITHM: {settings.ALGORITHM}")
    print(f"  过期时间: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} 分钟")
    
    # 从命令行参数获取 token
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"\n正在解码 Token: {token[:50]}...")
        
        try:
            payload = decode_access_token(token)
            if payload:
                print("\n✓ Token 解码成功！")
                print(f"\nPayload 内容:")
                for key, value in payload.items():
                    if key == "exp":
                        from datetime import datetime
                        exp_time = datetime.fromtimestamp(value)
                        now = datetime.now()
                        print(f"  {key}: {value} ({exp_time})")
                        if now.timestamp() > value:
                            print(f"    ⚠️ Token 已过期！当前时间: {now}")
                        else:
                            print(f"    ✓ Token 未过期，剩余时间: {int((value - now.timestamp()) / 60)} 分钟")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("\n✗ Token 解码失败！")
                print("\n可能的原因:")
                print("  1. SECRET_KEY 不匹配")
                print("  2. Token 已过期")
                print("  3. Token 格式错误")
                print("  4. Token 签名验证失败")
                print("\n建议:")
                print("  - 检查 SECRET_KEY 是否与登录时使用的相同")
                print("  - 尝试重新登录获取新的 Token")
        except Exception as e:
            print(f"\n✗ 解码时发生错误: {type(e).__name__}: {e}")
    else:
        print("\n使用方法:")
        print("  python check_token.py <token>")
        print("\n示例:")
        print("  python check_token.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

