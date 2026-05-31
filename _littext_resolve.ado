/*!
_littext_resolve: locate a packaged resource (a Python module or a data
file) on the adopath, robust to where Stata's net install actually places
force-installed files.

Background. net install does NOT keep a package's files together: it
distributes them into the PLUS letter/extension subdirectories (e.g.
littext.ado -> PLUS/l/, _littext_*.ado -> PLUS/_/, the Python modules into
their own subdirectory). They are therefore neither beside littext.ado nor
under a python/ subfolder of it. Reconstructing a path from littext.ado's
location is consequently wrong for an installed package.

The correct mechanism is findfile, which searches the whole adopath and is
exactly how force-installed files are meant to be located. We use it first.
The development tree is the one case findfile cannot serve directly: there
the modules live in <pkgdir>/python/ and <pkgdir>/data/, which are not on
the adopath. For that case we fall back to the layout relative to
littext.ado.

Syntax:
  _littext_resolve , subdir(name) name(file)

  subdir() is the development-layout subdirectory (python or data); it is
  used only in the fallback and in the error message.

Returns in r():
  r(path)   absolute path to the resolved file
  r(dir)    directory containing it, no trailing separator (suitable for
            sys.path insertion)

Exits r(601) with an actionable message if the file is found nowhere.
*/

program define _littext_resolve, rclass
    version 19.0
    syntax , SUBDIR(string) NAME(string)
    /* Strategy 1: installed (or otherwise on-adopath) layout. findfile
       searches the entire adopath, including the PLUS subdirectories that
       net install populates. */
    capture findfile "`name'"
    if _rc == 0 {
        local full `"`r(fn)'"'
        local nlen = length("`name'")
        local flen = length(`"`full'"')
        return local path `"`full'"'
        return local dir = substr(`"`full'"', 1, `flen' - `nlen' - 1)
        exit 0
    }
    /* Strategy 2: development layout. The file sits in <pkgdir>/subdir/,
       which is not itself on the adopath; locate it relative to
       littext.ado. */
    findfile "littext.ado"
    local adodir = subinstr(`"`r(fn)'"', "littext.ado", "", .)
    capture confirm file `"`adodir'`subdir'/`name'"'
    if _rc == 0 {
        return local dir  `"`adodir'`subdir'"'
        return local path `"`adodir'`subdir'/`name'"'
        exit 0
    }
    capture confirm file `"`adodir'`name'"'
    if _rc == 0 {
        local alen = length(`"`adodir'"')
        return local dir = substr(`"`adodir'"', 1, `alen' - 1)
        return local path `"`adodir'`name'"'
        exit 0
    }
    di as err `"littext: cannot locate `name'."'
    di as err `"        Not found on the adopath, nor in `adodir'`subdir', nor in `adodir'."'
    di as err "        Reinstall the package, or run: littext install, verbose"
    exit 601
end
