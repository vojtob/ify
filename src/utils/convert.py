import os
from pathlib import PureWindowsPath, Path
import subprocess
import shutil

movefiles = []

def __img_walk(args, source_path, destination_path, orig_extension, new_extension, onfile):
    if args.verbose:
        print('convert {0}({1}) -> {2}({3})'.format(str(source_path), orig_extension, str(destination_path), new_extension))
    # walk over files in from directory
    for (dirpath, _, filenames) in os.walk(source_path):
        # create destination directory
        d = Path(dirpath.replace(str(source_path), str(destination_path)))       
        d.mkdir(parents=True, exist_ok=True)
        # convert files with specific extension
        for f in [f for f in filenames if f.endswith(orig_extension)]:          
            # ffrom is original full name with path and orig extension
            ffrom = os.path.join(dirpath, f)
            # fto is destination full name with path and new extension
            fto = ffrom.replace(str(source_path), str(destination_path)).replace(orig_extension, new_extension)
            onfile(args, ffrom, fto, orig_extension, new_extension)

def onfile_convert_svg(args, fromfile, tofile, orig_extension, new_extension):
    # svg_command = str(Path(os.environ['IM_HOME'], 'magick')) + ' -density 144 {srcfile} {destfile}'
    density = 144
    if args.poster:
        density = int(density * args.poster)
    # svg_command = 'magick -density 144 {srcfile} {destfile}'
    svg_command = 'magick -density {density} {srcfile} {destfile}'
    cmd = svg_command.format(srcfile=fromfile, destfile=tofile, density=density)
    if args.debug:
        print(cmd)
    subprocess.run(cmd, shell=False)

def onfile_convert_uml(args, fromfile, tofile, orig_extension, new_extension):
    global movefiles
    uxf_command = str(Path('C:/', 'prg', 'Umlet', 'Umlet')) + ' -action=convert -format=png -filename="{srcfile}"'
    cmd = uxf_command.format(srcfile=fromfile)
    if args.debug:
        print(cmd)
    subprocess.run(cmd, shell=False)
    x = fromfile.replace(orig_extension, new_extension)
    movefiles.append((x, tofile))
   
def onfile_convert_mmd(args, fromfile, tofile, orig_extension, new_extension):
    # mmPath = os.path.join('C:/', 'prg', 'mermaid', 'node_modules', 'mermaid.cli', 'index.bundle.js')
    mmPath = str(Path('C:/prg/node_modules/.bin/mmdc'))
    mmd_command = '{mmpath} -w 1400 -i {srcfile} -o {destfile}'
    cmd = mmd_command.format(srcfile=fromfile, destfile=tofile, mmpath=mmPath)
    if args.debug:
        print(cmd)
    subprocess.run(cmd, shell=True)

def onfile_convert_plantuml(args, fromfile, tofile, orig_extension, new_extension):
    # mmPath = os.path.join('C:/', 'prg', 'mermaid', 'node_modules', 'mermaid.cli', 'index.bundle.js')
    pupath = str(Path('C:/ProgramData/chocolatey/lib/plantuml/tools/plantuml.jar'))
    # pucmd = 'java -jar {p} -tsvg {srcfile}'
    # cmd = pucmd.format(srcfile=fromfile, p=pupath)
    pucmd = 'cat {srcfile} | java -jar {p} -tsvg -pipe > {destfile}'
    cmd = pucmd.format(srcfile=fromfile, destfile=tofile, p=pupath)
    if args.debug:
        print(cmd)
    subprocess.run(cmd, shell=True)

def convert_svg(args):
    # convert svg files to png files
    __img_walk(args, 
        args.svgdir, args.exporteddir, 
        '.svg', '.png', onfile_convert_svg)

def convert_uml(args):
    # convert uxf files to png files
    global movefiles
    movefiles = []
    __img_walk(args, 
        args.sourcedir, args.exporteddir, 
        '.uxf', '.png', onfile_convert_uml)
    # move files
    if len(movefiles) < 1:
        if args.verbose:
            print('no uxf files generated')
    else:
        for (fromFile, toFile) in movefiles:
            if args.debug:
                print('move file {0} -> {1}'.format(fromFile, toFile))
            while True:
                try:
                    os.replace(fromFile, toFile)
                    break
                except (PermissionError, FileNotFoundError):
                    pass

def convert_mmd(args):
    # convert mm files to png files
    # args.problems.append('mermaid NOT ACTIVATED')
    __img_walk(args, 
        args.sourcedir, args.exporteddir, 
        '.mmd', '.png', onfile_convert_mmd)

def convert_plantuml(args):
    # convert plantUML files to SVG files
    # args.problems.append('mermaid NOT ACTIVATED')
    __img_walk(args, 
        args.sourcedir, args.svgdir, 
        '.puml', '.svg', onfile_convert_plantuml)

def mycopy(source_directory, destination_directory, args, ingore_dot_folders=True, onfile=None):
    """ copy files from source to destination

    optional parameter onfile is special handling function. If it is not specified (default), then file is
    copied from source to destination directory. If specified, it called for each file with argumentes sourcefilepath,
    destfilepath, debug and must handle copying file or generating or replacing or ...
    """

    if args.debug:
        print('copy {0} -> {1}'.format(str(source_directory), str(destination_directory)))
    # walk over files in from directory
    for (dirpath, dirnames, filenames) in os.walk(source_directory):
        # if debug:
        #     print('copy dirpath:', dirpath, Path(dirpath).name)
        if Path(dirpath).name.startswith('.'):
            # if debug:
            #     print('ignore')
            dirnames.clear()
            continue
        # create destination directory
        d = Path(dirpath.replace(str(source_directory), str(destination_directory)))
        d.mkdir(parents=True, exist_ok=True)
        
        # convert files with specific extension
        for f in filenames:
            sourcefile = Path(dirpath, f)
            destfile = str(sourcefile).replace(str(source_directory), str(destination_directory))
            relativepath = str(sourcefile).replace(str(source_directory), '')
            if onfile is not None:
                onfile(sourcefile, Path(destfile), relativepath, args)
            else:
                shutil.copy(str(sourcefile), destfile)