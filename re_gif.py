import sqlite3
import os
from PIL import Image

    ## resim işleme kısmının başlangıcı


def resize_gif(path):
    all_frames = extract_and_resize_frames(path)
    save_as = path

    if len(all_frames) == 1:
        print("Warning: only 1 frame found")
        all_frames[0].save(save_as, optimize=False)
    else:
        all_frames[0].save(save_as, optimize=True, save_all=True, append_images=all_frames[1:], quality=85, duration=1000)


def analyseImage(path):
    im = Image.open(path)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results


def extract_and_resize_frames(path):

    mode = analyseImage(path)['mode']

    im = Image.open(path)
    
    resize_to = (im.size[0] // 2, im.size[1] // 2)

    i = 0
    p = im.getpalette()
    last_frame = im.convert('RGBA')

    all_frames = []

    try:
        while True:

            if not im.getpalette():
                im.putpalette(p)

            new_frame = Image.new('RGBA', im.size)

            if mode == 'partial':
                new_frame.paste(last_frame)

            new_frame.paste(im, (0, 0), im.convert('RGBA'))

            new_frame.thumbnail(resize_to, Image.ANTIALIAS)
            all_frames.append(new_frame)


            i += 1
            last_frame = new_frame
            im.seek(im.tell() + 1)
    except EOFError:
        pass

    return all_frames

    ## resim işleme kısmının sonu




vt = sqlite3.connect('process_gifs.db') # veri tabanı yoksa kendisi oluşturur
db = 'process_gifs.db'

if not os.path.isfile(db):
    print('Böyle bir veritabanına erişilemedi.') # veri tabanına erişilemezse verilecek hata

else:
    print('Veritabanına başarıyla erişim sağlandı.')
    path = '/Users/mtahabahsi/Desktop/images' ## buraya giflerin bulunduğu dosyaların bulunduğu konum girilecek
    dirs = os.listdir(path) #giflerin bulunduğu klasörlerin listesi dirs değişkenine atılıyor (dizi olarak)
    
    c = vt.cursor() #veri tabanında işlem yapılabilmesi için cursor açılıyor 
    c.execute("""CREATE TABLE IF NOT EXISTS dosyalar (folder_name TEXT)""") # veri tabanı boş ise dosya isimlerinin tutulacağı tablo ve alanı oluşturuluyor
    vt.commit()

    for dir in dirs: #giflerin bulunduğu klasörlerin gezileceği loop
        if not dir.startswith('.'): #gizli dosyaların alınmaması için . ile başlayan klasörlere gidilmiyor
            images = os.listdir(path + "/" + dir) #gifin bulunduğu klasördeki resimler diziye atılıyor 
            for image in images:
                if ".gif" in image: # şu an kontrol edilen resmin gif olup olmadığı conductionu
                    c.execute("SELECT folder_name FROM dosyalar WHERE folder_name='" +  dir + "'") # daha önce işlenmiş mi diye veri tabanına bakılacak sorgu yazılıyor
                    temp = c.fetchone() # dönen değer bir değişkene atılıyor
                    if temp is None: # eğer daha önce işlenmemişse bu kontrole girecek
                        resize_gif(path + "/" + dir + "/" + image)
                        print(dir + " işlendi.")
                        c.execute(" INSERT INTO dosyalar(folder_name) VALUES('" + dir + "')")
                        vt.commit() 
                        print(dir + "veri tabanına yazıldı")
                        print("**********")
                        # resim işleniyor ve adı veri tabanına yazılıyor
                    else:
                        print("zaten işlenmiş gif " + dir)
    vt.close()