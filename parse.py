

import pathlib
import shutil


ROOTDIR = '.'


def proc_comment(doc, output, fig, subfig):
    """
    Processes the given document from the specified point and returns
    replacement string for the next N characters (N is returned).
    """
    i = doc.find("\n")

    # Retain empty comments
    if i < 0:
        return 2, "%\n", fig, subfig

    s = doc[:(i+1)]
    ts = "".join(s.split()) # Trim all whitespace

    # If only '%' on the line, keep it...
    if ts == ("%"*len(ts)):
        return len(s), s, fig, subfig
    else:
        return len(s), "", fig, subfig


def proc_newfig(doc, output, fig, subfig):
    r"""
    Process a '\begin{figure}' command.
    """
    s = r"\begin{figure}"
    return len(s), s, fig+1, 0


def proc_newfig_s(doc, output, fig, subfig):
    r"""
    Process a '\begin{figure*}' command.
    """
    s = r"\begin{figure*}"
    return len(s), s, fig+1, 0


def proc_filename(doc):
    """
    Returns the filename contained in a command with the format
      
      [...]{filename}
    
    where the ellipsis "..." can be anything.
    """
    i = 0
    add = 0
    if doc[0] == '[':
        i = doc.find(']')
        if i < -1:
            raise Exception("Parser exception: Cannot find closing ']' in graphics command.")
    else:
        add = 1

    d = doc[i:]
    op = d.find('{')
    cl = d.find('}')

    fname = d[(op+1):cl].strip()

    return (i+cl+1+add), i, fname

    
def proc_graphics(cmd, doc, output, fig, subfig, issubfig=False):
    r"""
    Process a graphics command.
    """
    l = len(cmd)
    # Identify file name
    N, optend, fname = proc_filename(doc[l:])
    # Copy file
    newname = proc_copy_fig(fname, output, fig, subfig, issubfig)

    print(" --> Replacing graphic '{}'...".format(newname))

    # Construct replacement command
    s = doc[:(l+optend+1)] + '{' + newname + '}'

    return l+N, s, fig, subfig+1


def proc_copy_fig(filename, output, fig, subfig, issubfig=False):
    """
    Copies the figure with the given filename to a new file named
    according to the (sub)figure number.
    """
    global ROOTDIR

    subfigcap = 'abcdefghijklmnopqrstuvwxyz'
    ext = pathlib.Path(filename).suffix

    if issubfig:
        newname = 'fig{:d}{}{}'.format(fig, subfigcap[subfig], ext)
    else:
        newname = 'fig{:d}{}'.format(fig, ext)

    shutil.copy(ROOTDIR / filename, '{}/{}'.format(output, newname))

    return newname


def proc_includegraphics_sub(doc, output, fig, subfig):
    r"""
    Process an '\includegraphics' command inside a '\begin{figure}'
    command with other graphics commands.
    """
    return proc_includegraphics(doc, output, fig, subfig, issubfig=True)


def proc_includegraphics(doc, output, fig, subfig, issubfig=False):
    r"""
    Process an '\includegraphics' command.
    """
    return proc_graphics(r'\includegraphics', doc, output, fig, subfig, issubfig)


def proc_overpic_sub(doc, output, fig, subfig):
    r"""
    Process a '\begin{overpic}' command inside a '\begin{figure}'
    command with other graphics commands.
    """
    return proc_overpic(doc, output, fig, subfig, issubfig=True)


def proc_overpic(doc, output, fig, subfig, issubfig=False):
    r"""
    Process a '\begin{overpic}' command.
    """
    return proc_graphics(r'\begin{overpic}', doc, output, fig, subfig, issubfig)


def proc_input(doc, output, fig, subfig):
    r"""
    Process an '\input' command.
    """
    global ROOTDIR

    cmd = r'\input'
    l = len(cmd)
    N, optend, fname = proc_filename(doc[l:])
    
    if '.' not in fname:
        fname += '.tex'

    fig, subfig = process_file(ROOTDIR / fname, output, fig, subfig)

    outname = pathlib.Path(output) / pathlib.Path(fname).name
    newcmd = r'\input{{{}}}'.format(outname.name)

    return l+N-1, newcmd, fig, subfig


CMDFIG = [r'\begin{figure}', r'\begin{figure*}', r'\includegraphics', r'\begin{overpic}']
FUNFIG = [proc_newfig, proc_newfig_s, proc_includegraphics, proc_overpic]


def mark(doc, keylist, typelist):
    """
    Create a list of indices to all occurences of the strings
    in 'keylist'.
    """
    pts = []

    for key, t in zip(keylist, typelist):
        pos = 0
        cont = True

        while cont:
            pos = doc.find(key, pos)
            if pos >= 0:
                pts.append((pos, t))
                pos += 1
            else:
                cont = False

    return sorted(pts, key=lambda tup : tup[0])


def mark_comments(doc):
    """
    Locate all comments in the document.
    """
    lst = mark(doc, ['%'], [proc_comment])

    pts = []
    for pt in lst:
        if pt[0] > 0 and doc[pt[0]-1] == "\\":
            continue
        else:
            pts.append(pt)

    return pts


def mark_figures(doc):
    """
    Locate all figure inclusions in the given document.
    """
    global CMDFIG, FUNFIG
    figs = mark(doc, CMDFIG, FUNFIG)

    newfigs = [proc_newfig, proc_newfig_s]

    l = len(figs)
    insubfig = False
    # Replace with subfigure equivalents where applicable
    for i in range(l):
        if figs[i][1] == proc_includegraphics:
            if insubfig or (i+1 < l and figs[i+1][1] not in newfigs):
                figs[i][1] = proc_includegraphics_sub
                insubfig = True
        elif figs[i][1] == proc_overpic:
            if insubfig or (i+1 < l and figs[i+1][1] not in newfigs):
                figs[i][1] = proc_overpic_sub
                insubfig = True
        else:
            insubfig = False

    return figs


def mark_inputs(doc):
    """
    Locate all '\input' in the given document.
    """
    return mark(doc, [r'\input'], [proc_input])


def process_file(file, output, fig=0, subfig=0):
    """
    Processes the given file and stores a (modified) copy of it
    in the output directory.

    :param str file: Name of file to process.
    :param str output: Name of directory in which to store the output.
    :param int fig: Starting figure index. An updated value is returned by this routine.
    """
    global ROOTDIR
    ROOTDIR = pathlib.Path(file).parent.absolute().resolve()

    print("Processing '{}'... ".format(str(pathlib.Path(file).relative_to(ROOTDIR))), end="")

    with open(file, 'r') as f:
        doc = f.read()

    # Locate comments, figures and inputs
    comm = mark_comments(doc)
    figs = mark_figures(doc)
    inps = mark_inputs(doc)

    print("")
    #print("(figures: {}, input: {})".format(len(figs), len(inps)))

    cmds = sorted(comm + figs + inps, key=lambda tup : tup[0])

    out = ""
    idx = 0
    for pos, proc in cmds:
        if pos > idx:
            out += doc[idx:pos]
            idx += pos-1
        # If this command has been commented out, we skip it...
        elif pos < idx:
            continue

        N, s, fig, subfig = proc(doc[pos:], output, fig, subfig)

        idx = pos+N
        out += s

    # Add remainder of file
    out += doc[idx:]

    outname = pathlib.Path(output) / pathlib.Path(file).name
    with open(outname, 'w') as f:
        f.write(out)

    return fig, subfig


