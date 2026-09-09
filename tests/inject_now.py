"""اجرای inject مستقیم daemon جدید برای تست live در Antigravity"""
import sys
sys.path.insert(0, 'daemon')
import antigravity_rtl_daemon

result = antigravity_rtl_daemon.check_and_inject()
print(f"Inject result: {'SUCCESS' if result else 'FAILED (Antigravity open?)'}")
