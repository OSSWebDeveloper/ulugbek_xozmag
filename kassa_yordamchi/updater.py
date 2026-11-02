"""Stage and apply authenticated updates from the shop server."""
import hashlib,io,json,os,shutil,subprocess,sys,time,urllib.request,uuid,zipfile
from pathlib import Path

ALLOWED={'agent.py','tray.py','updater.py','chek_print.ps1','etiketka_print.ps1','local_devices.py','versiya.txt','bizaropos.ico'}
def permitted(name):
    p=Path(name)
    return not p.is_absolute() and '..' not in p.parts and '\\' not in name and (name in ALLOWED or name.startswith('tray_deps/'))


def stage_update(root,config):
    request=urllib.request.Request(config['url']+'/qurilmalar/kassa-agent/yangila/',data=b'',headers={'Authorization':'Bearer '+config['token']},method='POST')
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=60) as response:
        data=response.read(32000001)
    if len(data)>32000000:raise ValueError('Yangilanish hajmi juda katta')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        files=manifest['files']
        if not files or any(not permitted(n) for n in files):raise ValueError('Yangilanish tarkibi noto‘g‘ri')
        if set(archive.namelist())!=set(files)|{'manifest.json'}:raise ValueError('Kutilmagan fayllar')
        blobs={n:archive.read(n) for n in files}
        if sum(len(b) for b in blobs.values())>80000000:raise ValueError('Yangilanish haddan tashqari katta')
        for n,b in blobs.items():
            if hashlib.sha256(b).hexdigest()!=files[n]:raise ValueError('Fayl tekshiruvi o‘tmadi')
        if all((root/n).exists() and hashlib.sha256((root/n).read_bytes()).hexdigest()==files[n] for n in files):return None
        stage=root/'.updates'/uuid.uuid4().hex;stage.mkdir(parents=True)
        for n,b in blobs.items():
            target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
        (stage/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        return stage


def apply(root,stage,pid):
    import ctypes
    kernel=ctypes.windll.kernel32
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_bool,ctypes.c_ulong]
    handle=kernel.OpenProcess(0x00100000,False,pid)
    if handle:
        kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
        if kernel.WaitForSingleObject(handle,90000)!=0:raise RuntimeError('Eski yordamchi hali yopilmadi')
        kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(handle)
    files=json.loads((stage/'manifest.json').read_text())['files']
    backup=stage/'backup';changed=[]
    try:
        for n,checksum in files.items():
            if not permitted(n) or hashlib.sha256((stage/n).read_bytes()).hexdigest()!=checksum:raise ValueError('Yangilanish tekshiruvi o‘tmadi')
        for n in files:
            target=root/n;old=backup/n;old.parent.mkdir(parents=True,exist_ok=True)
            existed=target.exists()
            if existed:shutil.copy2(target,old)
            changed.append((n,existed))
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(stage/n,target)
    except Exception:
        for n,existed in reversed(changed):
            if existed:shutil.copy2(backup/n,root/n)
            else:(root/n).unlink(missing_ok=True)
        raise
    finally:
        subprocess.Popen([sys.executable,str(root/'agent.py')],cwd=root,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    try:apply(root,Path(sys.argv[1]),int(sys.argv[2]))
    except Exception as exc:(root/'yangilanish-xato.txt').write_text(str(exc),encoding='utf-8')
