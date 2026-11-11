"""Ichki tarmoq (do'kondagi Wi-Fi) manzillari.

Do'kondagi boshqa kompyuterlar — masalan rang mashinasi yonidagisi — serverga
shu manzillar orqali ulanadi. Internet shart emas: router bo'lsa bas.

Django'ga bog'liq emas: ishga tushirgich (ishga_tushir.py) uni server
ko'tarilishidan oldin ham chaqiradi.
"""
import ipaddress
import socket


def _ichkimi(ip):
    """Ichki tarmoq manzilimi (192.168.x.x, 10.x.x.x, 172.16–31.x.x)."""
    try:
        manzil = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return (manzil.version == 4 and manzil.is_private
            and not manzil.is_loopback and not manzil.is_link_local)


def ip_manzillar():
    """Shu kompyuterning ichki tarmoqdagi IPv4 manzillari — asosiysi birinchi."""
    ipler = []
    try:
        # Paket jo'natilmaydi: tizim faqat qaysi tarmoq kartasidan chiqishni tanlaydi.
        # Wi-Fi ham, kabel ham ulangan bo'lsa routerga boradigani birinchi turadi.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ipler.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        ipler += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass

    natija = []
    for ip in ipler:
        if _ichkimi(ip) and ip not in natija:
            natija.append(ip)
    return natija


def doimiy_manzil(port=5555, scheme='http'):
    """Ishlayotgan LAN IPni tanlash: mavjud bo'lmagan statik IPni reklama qilmaydi."""
    import json
    from pathlib import Path
    file = Path(__file__).resolve().parent.parent / 'qurilmalar_data/kassalar.json'
    try:
        configured = json.loads(file.read_text(encoding='utf-8')).get('server_ip', '')
    except (OSError, ValueError, TypeError):
        configured = ''
    available = ip_manzillar()
    # IP haqiqatan ham tarmoq kartasida bo'lsagina undan foydalanamiz.
    ip = configured if configured in available else (available[0] if available else '')
    return f'{scheme}://{ip}:{port}' if ip else ''



def manzillar(port):
    """Boshqa kompyuterning brauzeriga yoziladigan manzillar: IP bilan va nom bilan.

    IP o'zgarishi mumkin (router har safar boshqasini beradi), kompyuter nomi
    esa o'zgarmaydi — lekin nom bilan har doim ham topilavermaydi. Shuning uchun
    ikkalasi ham ko'rsatiladi. Tarmoqqa ulanmagan bo'lsa bo'sh ro'yxat.
    """
    ipler = ip_manzillar()
    if not ipler:
        return []
    natija = [f"http://{ip}:{port}/" for ip in ipler]
    nom = socket.gethostname()
    if nom and nom.isascii():
        natija.append(f"http://{nom}:{port}/")
    return natija
