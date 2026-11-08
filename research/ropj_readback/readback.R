# A direct, read-only call to an existing official Ropj installation.
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 6L) stop("Expected input, output, book, rows, columns, version")
if (!requireNamespace("Ropj", quietly=TRUE)) stop("Ropj is not installed; no installation attempted")
version <- packageDescription("Ropj")$Version
if (!identical(version, args[6])) stop("Untested Ropj version")
project <- Ropj::read.opj(args[1], encoding="latin1")
if (!identical(names(project), args[3])) stop("Expected exactly one returned workbook")
sheet <- project[[1L]]
if (!is.data.frame(sheet)) stop("Expected a single-sheet workbook")
if (nrow(sheet) != as.integer(args[4]) || ncol(sheet) != as.integer(args[5]))
    stop("Unexpected worksheet dimensions")
# Never coerce a mixed/text column back to numeric: that would conceal rounding.
if (!all(vapply(sheet, function(x) identical(typeof(x), "double"), TRUE)))
    stop("Non-double columns: mixed/text column formatting cannot prove numeric precision")
comments <- attr(sheet, "comment", exact=TRUE)
commands <- attr(sheet, "commands", exact=TRUE)
if (!is.character(comments) || length(comments) != ncol(sheet)) stop("Missing column metadata")
if (!is.character(commands) || length(commands) != ncol(sheet)) stop("Missing command metadata")
if (anyNA(commands) || any(commands != "")) stop("Column commands are not empty")
if (anyNA(comments)) stop("Missing column labels")
values <- unlist(sheet, use.names=FALSE)
writeBin(values, file.path(args[2], "values.f64le"), size=8L, endian="little")
writeBin(as.raw(is.na(values)), file.path(args[2], "missing.u8"))
write.table(data.frame(column=seq_along(sheet), short_name=names(sheet),
                       comment=comments, command=commands),
            file.path(args[2], "metadata.tsv"), sep="\t", row.names=FALSE,
            quote=TRUE, qmethod="double", fileEncoding="UTF-8")
write.table(data.frame(ropj_version=version, r_version=R.version.string,
                       rows=nrow(sheet), columns=ncol(sheet)),
            file.path(args[2], "reader.tsv"), sep="\t", row.names=FALSE,
            quote=TRUE, qmethod="double", fileEncoding="UTF-8")
