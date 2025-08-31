import os
import subprocess
import re
import sys
import argparse

def find_ffmpeg():
    """
    Пытается найти ffmpeg в системе
    """
    possible_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('SystemDrive', 'C:'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        'ffmpeg.exe',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def parse_cue_file(cue_file_path):
    """
    Парсит CUE файл и извлекает информацию о треках
    """
    tracks = []
    current_file = None
    current_track = None
    
    # Пробуем разные кодировки
    encodings = ['utf-8', 'cp1251', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(cue_file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        # Если ни одна кодировка не подошла, используем замену ошибок
        with open(cue_file_path, 'r', encoding='cp1251', errors='replace') as f:
            lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        
        if not line or line.startswith('REM'):
            continue
            
        if line.startswith('FILE'):
            match = re.search(r'FILE "(.*?)"', line)
            if match:
                current_file = match.group(1)
        
        elif line.startswith('TRACK'):
            if current_track:
                tracks.append(current_track)
            current_track = {
                'file': current_file,
                'title': f'track_{len(tracks) + 1:02d}',
                'performer': 'Unknown Artist'
            }
        
        elif line.startswith('TITLE'):
            match = re.search(r'TITLE "(.*?)"', line)
            if match and current_track:
                current_track['title'] = match.group(1)
        
        elif line.startswith('PERFORMER'):
            match = re.search(r'PERFORMER "(.*?)"', line)
            if match and current_track:
                current_track['performer'] = match.group(1)
        
        elif line.startswith('INDEX 01'):
            match = re.search(r'INDEX 01 (\d+):(\d+):(\d+)', line)
            if match and current_track:
                minutes, seconds, frames = map(int, match.groups())
                total_seconds = minutes * 60 + seconds + frames / 75.0
                current_track['start_time'] = total_seconds
    
    if current_track:
        tracks.append(current_track)
    
    for i in range(len(tracks) - 1):
        tracks[i]['end_time'] = tracks[i + 1]['start_time']
    
    return tracks

def safe_filename(name):
    """Очищает имя файла от недопустимых символов"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def run_ffmpeg_silent(cmd):
    """Запускает ffmpeg без вывода прогресса (чтобы избежать проблем с кодировкой)"""
    try:
        # Используем subprocess.run с подавлением вывода
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=False,  # Важно: text=False для бинарного вывода
            timeout=3600  # Таймаут 1 час на трек
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Таймаут выполнения команды")
        return False
    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        return False

def split_ape_file(cue_file_path, output_dir="output", ffmpeg_path=None):
    """
    Основная функция для разделения APE файла
    """
    if not os.path.exists(cue_file_path):
        print(f"Ошибка: CUE файл {cue_file_path} не найден!")
        return False
    
    if ffmpeg_path:
        if not os.path.exists(ffmpeg_path):
            print(f"Ошибка: ffmpeg не найден по указанному пути: {ffmpeg_path}")
            return False
    else:
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            print("Ошибка: ffmpeg не найден в системе!")
            print("Установите ffmpeg или укажите путь с помощью --ffmpeg")
            return False
    
    print(f"Используется ffmpeg: {ffmpeg_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    tracks = parse_cue_file(cue_file_path)
    
    if not tracks:
        print("Не удалось извлечь информацию о треках")
        return False
    
    cue_dir = os.path.dirname(cue_file_path)
    ape_file_path = os.path.join(cue_dir, tracks[0]['file'])
    
    if not os.path.exists(ape_file_path):
        print(f"Ошибка: APE файл {ape_file_path} не найден!")
        return False
    
    print(f"Найдено {len(tracks)} треков")
    print(f"Исходный файл: {ape_file_path}")
    
    successful_tracks = 0
    
    for i, track in enumerate(tracks, 1):
        start_time = track.get('start_time', 0)
        end_time = track.get('end_time')
        
        title = track.get('title', f'track_{i:02d}')
        performer = track.get('performer', 'Unknown Artist')
        
        safe_title = safe_filename(title)
        safe_performer = safe_filename(performer)
        
        output_filename = f"{i:02d} - {safe_performer} - {safe_title}.flac"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\nОбработка трека {i}: {performer} - {title}")
        
        cmd = [
            ffmpeg_path,
            '-i', ape_file_path,
            '-ss', str(start_time),
        ]
        
        if end_time:
            cmd.extend(['-to', str(end_time)])
        
        cmd.extend([
            '-c:a', 'flac',
            '-compression_level', '8',
            '-metadata', f'title={title}',
            '-metadata', f'artist={performer}',
            '-metadata', f'track={i}/{len(tracks)}',
            '-y',
            output_path
        ])
        
        # Запускаем без вывода прогресса
        success = run_ffmpeg_silent(cmd)
        
        if success:
            print(f"✓ Успешно создан: {output_filename}")
            successful_tracks += 1
        else:
            print(f"✗ Ошибка при создании: {output_filename}")
    
    print(f"\nОбработка завершена! Успешно: {successful_tracks}/{len(tracks)}")
    return successful_tracks > 0

def main():
    parser = argparse.ArgumentParser(
        description='Разделение APE файла на треки с использованием CUE файла',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  python ape_splitter.py album.cue
  python ape_splitter.py album.cue -o "C:\\Music" --ffmpeg "C:\\ffmpeg\\bin\\ffmpeg.exe"
        '''
    )
    
    parser.add_argument('cue_file', help='Путь к CUE файлу')
    parser.add_argument('-o', '--output', default='output', help='Выходная директория')
    parser.add_argument('--ffmpeg', help='Путь к ffmpeg.exe')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.cue_file):
        print(f"Ошибка: CUE файл '{args.cue_file}' не найден!")
        sys.exit(1)
    
    success = split_ape_file(args.cue_file, args.output, args.ffmpeg)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
