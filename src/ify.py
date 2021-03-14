import argparse
from pathlib import PureWindowsPath, Path
import shutil
import subprocess

# import lxml.etree as ET

from utils import convert, img_processing

def log(args, message):
    message_format = '{args.projectname}: {message}'
    if hasattr(args, 'file') and args.file is not None:
        message_format = message_format + ' for file {args.file}'
    print(message_format.format(args=args, message=message))

def __add_project(args):
    if args.projectdir is None:
        args.projectdir = Path.cwd().parent
    else:
        args.projectdir = Path(args.projectdir)
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
    parser.add_argument('-pd', '--projectdir', help='set project explicitly')
    parser.add_argument('-v', '--verbose', help='to be more verbose', action='store_true')
    parser.add_argument('-d', '--debug', help='add debug info, very low level', action='store_true')
    parser.add_argument('-f', '--file', help='process only this one file')
    subparsers = parser.add_subparsers(help='command help')

    parser_clean = subparsers.add_parser('clean', help='clean all generated files and folders')
    parser_clean.set_defaults(command='clean')

    parser_archi = subparsers.add_parser('archi', help='export images from archimate tool')
    parser_archi.set_defaults(command='archi')
    parser_archi.add_argument('-f', '--file', help='process only this one file')

    parser_icons = subparsers.add_parser('icons', help='add icons to images based on src_doc/docs/img/images.json')
    parser_icons.set_defaults(command='icons')
    parser_icons.add_argument('-f', '--file', help='process only this one file')

    parser_areas = subparsers.add_parser('areas', help='create image with focused area based on src_doc/docs/img/img_focus.json')
    parser_areas.set_defaults(command='areas')
    parser_areas.add_argument('-f', '--file', help='process only this one file')

    parser_publish = subparsers.add_parser('publish', help='publish image files')
    parser_publish.set_defaults(command='publish')

    parser_umlet = subparsers.add_parser('umlet', help='umlet -> png')
    parser_umlet.set_defaults(command='umlet')

    parser_mermaid = subparsers.add_parser('mermaid', help='mermaid images -> png')
    parser_mermaid.set_defaults(command='mermaid')

    args = parser.parse_args()
    args = __add_project(args)
    if args.debug:
        args.verbose = True

    if not hasattr(args, 'command'):
        args.command = 'all'
    log(args, 'starts with the command ' + args.command)

    if args.command=='clean':
        log(args, 'start cleaning')
        for dirname in ['temp/img_all', 'temp/img_rec', 'temp/img_exported', 'temp/img_exported_svg', 'temp/img_icons']: # 'release/img', 
            p = args.projectdir / dirname
            if p.exists():
                shutil.rmtree(p)
                if args.verbose:
                    print('delete', p)
        log(args, 'done cleaning')

    if (args.command=='archi') or (args.command=='all'):
        log(args, 'start archi')
        # export from archi
        print('export images from archi - OPEN ARCHI!')
        cmd = '"{autoit_path}" {script_path} {project_path}'.format(
            autoit_path= PureWindowsPath('C:/Program Files (x86)/AutoIt3/AutoIt3_x64.exe'), 
            script_path=args.ifypath / 'src' / 'autoit' / 'exportImages.au3', 
            project_path=args.projectdir)
        if args.file is not None:
            cmd = cmd + ' ' + args.file
        if args.debug:
            print(cmd)
        subprocess.run(cmd, shell=False)
        # convert from svg to png
        convert.convert_svg(args)
        # dimg.doit(args)
        log(args, 'done archi')
    
    if (args.command=='icons') or (args.command=='all'):
        log(args, 'start icons')
        img_processing.add_icons(args)
        log(args, 'done icons')
    
    if (args.command=='areas') or (args.command=='all'):
        log(args, 'start areas')
        img_processing.add_areas(args)
        log(args, 'done areas')
    
    if (args.command=='umlet'):
        log(args, 'start umlet')
        # convert from uxf to png
        convert.convert_uml(args)
        log(args, 'done umlet')
    
    if (args.command=='mermaid'):
        log(args, 'start mermaid')
        # convert from mmd to png
        convert.convert_mmd(args)
        log(args, 'done mermaid')

    # if (args.command=='publish') or (args.command=='all'):
    log(args, 'start merging images')
    # publish images to release dir
    # imgspath = args.projectdir / 'release' / 'img'
    imgspath = args.projectdir / 'temp' / 'img_all'
    imgspath.mkdir(parents=True, exist_ok=True)
    # copy png images from src  
    # copy exported images
    convert.mycopy(args.projectdir / 'temp' / 'img_exported', imgspath, args)
    # overwrite them with images with icons
    convert.mycopy(args.projectdir / 'temp' / 'img_icons', imgspath, args)
    # copy areas images
    convert.mycopy(args.projectdir / 'temp' / 'img_areas', imgspath, args)
    log(args, 'done merginf images')

    if (args.command=='align'):
        log(args, 'start align')
        # align elements in archimate file
        # modelname = args.projectname+'.archimate'
        # dom = ET.parse( str(args.projectdir / 'src_doc' / 'model' / modelname))
        # xslt = ET.parse(str(args.docoolpath / 'src' / 'xslt' / 'align2grid.xsl'))
        # transform = ET.XSLT(xslt)
        # newdom = transform(dom)
        # modelname2 = args.projectname+'2.archimate'
        # with open(args.projectdir / 'src_doc' / 'model' / modelname2, 'w', encoding='UTF-8') as fout:
        #     fout.write(ET.tostring(newdom, encoding='unicode', method='xml')) #, pretty_print=True
        log(args, 'stop align')

    if args.problems:
        print('\nify: DONE ... with PROBLEMS !!')
        for p in args.problems:
            print('  ', p)
    else:
        print('\nify: DONE ... OK')
