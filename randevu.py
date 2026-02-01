import asyncio
import base64
import requests
import os
from playwright.async_api import async_playwright

CONFIG = {
    'member_id': 'IT42249322416',
    'email': 'erenrezecetin@gmail.com',
    'password': 'r%yLWf*E3B#YJs6D',
    'claude_api_key': os.environ.get('CLAUDE_API_KEY', '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'),
    'telegram_token': os.environ.get('TELEGRAM_TOKEN', '7040887732:AAFV_v3HYMZXyksvt3bKGux6HBVG3XTzNB8'),
    'telegram_chat_id': os.environ.get('TELEGRAM_CHAT_ID', '1199788938'),
}

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
    requests.post(url, json={'chat_id': CONFIG['telegram_chat_id'], 'text': mesaj})
    print(f"Telegram: {mesaj}")

def captcha_coz(base64_img):
    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'Content-Type': 'application/json',
            'x-api-key': CONFIG['claude_api_key'],
            'anthropic-version': '2023-06-01'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 50,
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': base64_img}},
                    {'type': 'text', 'text': 'CAPTCHA. 4 rakam var. Sadece rakamları yaz:'}
                ]
            }]
        }
    )
    result = response.json()
    kod = ''.join(filter(str.isdigit, result['content'][0]['text']))
    return kod

async def main():
    telegram_gonder("🚀 Randevu kontrolü başladı...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Login sayfasına git
            print("Login sayfasına gidiliyor...")
            await page.goto('https://it-tr-appointment.idata.com.tr/tr/login', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Cloudflare kontrolü
            content = await page.content()
            if 'cloudflare' in content.lower() and 'blocked' in content.lower():
                telegram_gonder("❌ Cloudflare engelledi")
                await browser.close()
                return
            
            print("Sayfa yüklendi, form dolduruluyor...")
            
            # Form doldur
            await page.fill('#memberId', CONFIG['member_id'])
            await page.fill('#email', CONFIG['email'])
            await page.fill('#password', CONFIG['password'])
            
            # CAPTCHA çöz
            captcha_img = page.locator('img[src^="data:image"]')
            if await captcha_img.count() > 0:
                src = await captcha_img.get_attribute('src')
                base64_data = src.split(',')[1]
                
                print("CAPTCHA çözülüyor...")
                captcha_kod = captcha_coz(base64_data)
                print(f"CAPTCHA: {captcha_kod}")
                
                await page.fill('#mailConfirmCodeControl', captcha_kod)
            
            # Giriş butonuna bas
            await page.click('#giris')
            await page.wait_for_timeout(3000)
            
            # Tamam butonuna bas
            tamam_btn = page.locator('.swal2-confirm')
            if await tamam_btn.count() > 0:
                await tamam_btn.click()
                await page.wait_for_timeout(2000)
            
            # Email kodu bekle (Gmail'den Telegram'a düşecek)
            telegram_gonder("📧 Email kodu bekleniyor... Gmail'den Telegram'a düşecek")
            
            # Burada email kodu için bekleme yapılabilir
            # Şimdilik manuel devam
            
            telegram_gonder("✅ Login işlemi tamamlandı")
            
        except Exception as e:
            telegram_gonder(f"❌ Hata: {str(e)}")
            print(f"Hata: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
