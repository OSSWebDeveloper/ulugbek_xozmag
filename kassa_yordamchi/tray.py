"""BizaroPOS cashier tray menu; runs on the Windows main thread."""
import json
import sys
import webbrowser


def run_tray(root, config, stop, state):
    sys.path.insert(0,str(root/'tray_deps'))
    import pystray
    from pystray._util import win32
    from PIL import Image

    restart=[False]
    class LeftMenuIcon(pystray.Icon):
        def _on_notify(self,wparam,lparam):
            if lparam==win32.WM_LBUTTONUP:
                lparam=win32.WM_RBUTTONUP
            return super()._on_notify(wparam,lparam)

    def close(icon,item):
        stop.set();icon.stop()

    def reboot(icon,item):
        restart[0]=True;close(icon,item)

    updating=[False]
    def update(icon,item):
        if updating[0]:return
        updating[0]=True
        def work():
            try:
                from updater import stage_update
                icon.notify('Serverdan yangilanish olinmoqda…','BizaroPOS Kassa')
                stage=stage_update(root,config)
                if stage is None:
                    icon.notify('Dastur yangilangan. Yangi o‘zgarish yo‘q.','BizaroPOS Kassa')
                else:
                    restart[0]=str(stage)
                    close(icon,item)
            except Exception as exc:icon.notify(str(exc)[:200],'Yangilash bajarilmadi')
            finally:updating[0]=False
        import threading
        threading.Thread(target=work,daemon=True).start()

    def select(name):
        def choose(icon,item):
            config['printer']=name
            path=root/'kassa.json';temp=path.with_suffix('.tmp')
            temp.write_text(json.dumps(config,ensure_ascii=True),encoding='ascii');temp.replace(path)
            state['refresh']=True
            icon.notify('Chek printeri: '+(name or 'Avtomatik'),'BizaroPOS Kassa')
        return choose

    def printer_items():
        yield pystray.MenuItem('Avtomatik',select(''),checked=lambda item:not config.get('printer'))
        for printer in state['printers']:
            name=printer['nom']
            yield pystray.MenuItem(name.replace('&','&&'),select(name),checked=lambda item,n=name:config.get('printer')==n)

    version=(root/'versiya.txt').read_text(encoding='utf-8').strip()
    icon=LeftMenuIcon('BizaroPOSKassa',Image.open(root/'bizaropos.ico'),
        'BizaroPOS '+config.get('kassir','Kassa'),pystray.Menu(
        pystray.MenuItem('Kassani ochish',lambda icon,item:webbrowser.open(config['url'])),
        pystray.MenuItem('Chek printerini tanlash',pystray.Menu(printer_items)),
        pystray.MenuItem('Printerlarni yangilash',lambda icon,item:state.update(refresh=True)),
        pystray.MenuItem('Dasturni yangilash',update),
        pystray.MenuItem('Yordamchini qayta ishga tushirish',reboot),
        pystray.MenuItem('Yordamchini yopish',close),
        pystray.MenuItem('Dastur versiyasi: '+version,None,enabled=False)))
    icon.run()
    return restart[0]
