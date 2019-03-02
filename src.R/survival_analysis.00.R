# Perform Cox proportional hazards regression analysis of survival data

# Copyright (c) 2018 Aubrey Barnard.  This is free, open software
# released under the MIT License.  (See `LICENSE.txt` for details.)

library(survival)

# Check and get command line arguments
args = commandArgs(trailingOnly=TRUE)
if (length(args) != 1) {
    cat("Error: Incorrect command line arguments\n", file=stderr())
    cat("Usage: <data-file>\n", file=stderr())
    quit(status=1)
}
data_filename = args[1]

# Read the data
data = read.table(data_filename, header=TRUE, sep="|")

# Fit a Cox proportional hazards model to the data
cox_reg = coxph(Surv(lo, hi, out) ~ exp, data=data)

# Output a summary of the model
summary(cox_reg)
