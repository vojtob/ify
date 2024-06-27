import argparse
from pathlib import PureWindowsPath, Path
import shutil

from utils import convert, img_processing

def log(args, message):
    message_format = '{args.projectname}: {message}'
    if hasattr(args, 'file') and args.file is not None:
        message_format = message_format + ' for file {args.file}'
    print(message_format.format(args=args, message=message))

def __add_project(args):
    if not 'projectdir' in args:
        args.projectdir = Path.cwd().parent
        if args.projectdir.stem == 'utils':
            args.projectdir = args.projectdir.parent
        if args.projectdir.stem == 'img':
            args.projectdir = args.projectdir.parent
        if args.projectdir.stem == 'src_doc':
            args.projectdir = args.projectdir.parent
    else:
        args.projectdir = Path(args.projectdir)

    args.destdir = args.projectdir / 'temp'

    args.alldir   = args.destdir / 'img_all'
    args.pngdir   = args.destdir / 'img_png'
    args.iconsdir = args.destdir / 'img_icons'
    args.areasdir = args.destdir / 'img_areas'
    args.recdir   = args.destdir / 'img_rec'
    args.bwdir    = args.destdir / 'img_BW'

    args.iconssourcedir = Path('C:/Projects_src/resources/dxc-icons')
    args.projectname = args.projectdir.stem
    args.ifypath = Path(__file__).parent.parent
    args.problems = []

    if args.verbose:
        print('{args.projectname}: {args.projectdir}'.format(args=args))
    if args.debug:
        print('docool path: {0}'.format(args.ifypath))

    return args

if __name__ == '__main__':
    print('ify: START\n')    
    
    parser = argparse.ArgumentParser(prog='ify', description='architecture images, icons, ...')
    # parser.add_argument('-pd', '--projectdir', help='set project explicitly')
    # parser.add_argument('command', choices=['all', 'clean', 'archi', 'svg', 'icons', 'areas', 'publish', 'umlet', 'mermaid'], help='what to do')
    parser.add_argument('-v', '--verbose', help='to be more verbose', action='store_true')
    parser.add_argument('-d', '--debug', help='add debug info, very low level', action='store_true')
    parser.add_argument('-p', '--poster', help='bigger dpi for posters, set scale e.g. 4', type=float)
    parser.add_argument('-f', '--file', help='process only this one file')
    subparsers = parser.add_subparsers(help='command help')

    parser_clean = subparsers.add_parser('clean', help='clean all generated files and folders')
    parser_clean.set_defaults(command='clean')

    parser_icons = subparsers.add_parser('icons', help='add icons to images based on src_doc/docs/img/images.json')
    parser_icons.set_defaults(command='icons')
    # # parser_icons.add_argument('-f', '--file', help='process only this one file')

    parser_areas = subparsers.add_parser('areas', help='create image with focused area based on src_doc/docs/img/img_focus.json')
    parser_areas.set_defaults(command='areas')
    # # parser_areas.add_argument('-f', '--file', help='process only this one file')

    parser_mermaid = subparsers.add_parser('rec', help='aby som videl identifikaciu obdlznikov')
    parser_mermaid.set_defaults(command='rec')

    parser_mermaid = subparsers.add_parser('test', help='pre testovanie novej funkcionality')
    parser_mermaid.set_defaults(command='test')

    # parser_publish = subparsers.add_parser('publish', help='publish image files')
    # parser_publish.set_defaults(command='publish')

    args = parser.parse_args()
    print(args)
    args = __add_project(args)
    if args.debug:
        args.verbose = True

    if not hasattr(args, 'command'):
        args.command = 'all'
    log(args, 'starts with the command ' + args.command)

    if args.command=='clean':
        log(args, 'start cleaning')
        for dirname in [args.alldir, args.iconsdir, args.areasdir, args.recdir, args.bwdir]:
            p = args.projectdir / dirname
            if p.exists():
                shutil.rmtree(p)
                if args.verbose:
                    print('delete', p)
        log(args, 'done cleaning')

    if (args.command=='icons') or (args.command=='all'):
        log(args, 'start icons')
        img_processing.add_decorations(args, 'icons')
        log(args, 'done icons')
    
    if (args.command=='areas') or (args.command=='all'):
        log(args, 'start areas')
        img_processing.add_decorations(args, 'areas')
        log(args, 'done areas')

    if (args.command=='rec'):
        log(args, 'start rectangles identification')
        img_processing.show_rectangles(args)
        log(args, 'done test')

    if (args.command=='test'):
        log(args, 'start test')
        # test functionality
        img_processing.add_decorations(args, 'test')
        log(args, 'done test')

    if args.command !='clean':
        # if (args.command=='publish') or (args.command=='all'):
        # publish images to img_all dir
        log(args, 'start merging images')
        args.alldir.mkdir(parents=True, exist_ok=True)
        # copy png images - this is in image_convert
        # convert.mycopy(args.pngdir, args.alldir, args)
        # overwrite images with images with icons
        convert.mycopy(args.iconsdir, args.alldir, args)
        # copy areas images
        convert.mycopy(args.areasdir, args.alldir, args)
        log(args, 'done merginf images')

    if args.problems:
        print('\nify: DONE ... with PROBLEMS !!')
        for p in args.problems:
            print('  ', p)
    else:
        print('\nify: DONE ... OK')
