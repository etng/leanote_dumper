# encoding=utf-8
import os
import re
import json
import pypinyin
import requests
import time
import datetime
import logging
logger = logging.getLogger(__name__)


base = os.path.expanduser('~/Library/Application Support/Leanote/nedb55')
save_base = './data'
images_subdir = 'images'
attachs_subdir = 'attachs'
images_base = os.path.join(save_base, images_subdir)
attachs_base = os.path.join(save_base, attachs_subdir)
images = {}
attachs = {}
image_ids = {}


def format_ts(ts):
    dt = datetime.datetime.fromtimestamp(ts / 1000.0)
    return dt.strftime('%Y-%m-%dT%H:%M:%S+08:00')


def download_image(file_id, filename, token, api='image'):
    global images, attachs
    if api == 'image' and file_id in images:
        logger.debug(u'image {} exists'.format(file_id))
        return images[file_id]
    if api == 'attach' and file_id in attachs:
        logger.debug(u'attach {} exists'.format(file_id))
        return attachs[file_id]
    url = 'https://leanote.com/api/file/{}?fileId={}&token={}'.format(
        'getAttach' if api == 'attach' else 'getImage',
        file_id,
        token
    )
    fullpath = os.path.join(images_base if api == 'image' else attachs_base, filename)
    if not os.path.exists(fullpath):
        while True:
            try:
                response = requests.get(url, timeout=(3, 27.3))
                print u'downloading {} to {}'.format(url, fullpath)
                with open(fullpath, 'wb') as f:
                    f.write(response.content)
                logger.debug(u'{} {} downloaded'.format(api, file_id))
                break
            except:
                pass
    return u'{}/{}'.format(
        images_subdir if api == 'image' else attachs_subdir,
        filename
    )


def format_content(content):
    '''
    ![双拼-keyboard.png](leanote://file/getImage?fileId=57575690ab644141b102bd6e)
    '''
    global user_token
    pattern = re.compile('\!\[([^\]]*)\]\(leanote:\/\/file\/getImage\?fileId=(.*?)\)')

    def replacer(m):
        name = m.group(1)
        fileId = m.group(2)
        filename = download_image(image_ids.get(fileId), name, user_token, 'image')
        return u'![{}]({})'.format(name, filename)
    # if re.search(pattern, content):
    #     import ipdb;ipdb.set_trace()
    return re.sub(pattern, replacer, content)



def make_slug(title):
    return '_'.join(map(lambda _:_.strip().replace('/', '_').replace(' ', '_'), pypinyin.lazy_pinyin(title, style=pypinyin.STYLE_TONE2)))


def save_note(row):
    # if row.get('Attachs'):
    #     import ipdb;ipdb.set_trace()

    try:
        title = row.get('Title', u'无标题')
        ext = '.md' if row.get('IsMarkdown', True) else '.htm'
        metas = [
            ('Title', [title],),
            ('Category', [note_books.get(row.get('NotebookId'))],),
            ('Tags', filter(None, row.get('Tags') or []),),
            ('CreatedTime', [format_ts(row['CreatedTime']['$$date'])],),
            ('PublicTime', [row.get('PublicTime')],),
        ]
        for attach in row.get('Attachs', []):
            metas.append(['Attach', [u'{} {}'.format(
                attach['Title'],
                download_image(attach['ServerFileId'], attach['Title'], user_token, 'attach')
            )]])
        seq = 0
        slug = make_slug(title)
        while True:
            fullpath = os.path.join(save_base, u''.join([slug, str(seq or ''), ext]))
            if not os.path.exists(fullpath):
                break
            seq += 1
        with open(fullpath, 'wb') as f:
            for header, values in metas:
                f.write(u'{}: {}'.format(header, u','.join(map(unicode, values))).encode('utf-8'))
                f.write("\n")
            f.write("\n")
            f.write("\n")
            f.write(u"-" * 3)
            f.write("\n")
            f.write("\n")
            f.write(format_content(row.get('Content', '')).encode('utf-8'))

    except Exception as e:
        print e, row
        import ipdb;ipdb.set_trace()


if __name__ == '__main__':
    users = map(json.loads, open(os.path.join(base, 'users.db')).readlines())
    user_id = users[0]['UserId']
    user_token = users[0]['Token']
    for _ in [save_base, images_base, attachs_base]:
        os.path.exists(_) or os.makedirs(_)
    attachs = map(json.loads, open(os.path.join(base, user_id, 'attachs.db')).readlines())
    note_books = {}
    for _ in map(json.loads, open(os.path.join(base, user_id, 'notebooks.db')).readlines()):
        note_books[_['NotebookId']] = _['Title']
    for _ in map(json.loads, open(os.path.join(base, user_id, 'images.db')).readlines()):
        if _['ServerFileId']:
            images[_['ServerFileId']] = download_image(_['ServerFileId'], _['Name'], user_token, 'image')
        image_ids[_['FileId']] = _['ServerFileId']

    for _ in map(json.loads, open(os.path.join(base, user_id, 'attachs.db')).readlines()):
        if _['ServerFileId']:
            attachs[_['FileId']] = download_image(_['ServerFileId'], _['Name'], user_token, 'attach')
    records = map(json.loads, open(os.path.join(base, user_id, 'notes.db')).readlines())
    map(save_note, records)
