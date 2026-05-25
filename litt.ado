/*!
litt: alias for the littext command.

This file is a thin wrapper that forwards all arguments and options unchanged
to littext. The two commands are functionally identical. 
`litt` is a convenience alias for litdiscover. 
See `help litdiscover' for full documentation.

Examples (equivalent):
    litt example, clear
    littext example, clear

    litt analyze, text(abstract) id(article_id)
    littext analyze, text(abstract) id(article_id)

    litt graph, type(map)
    littext graph, type(map)
*/

program define litt
    version 19.0
    littext `0'
end
