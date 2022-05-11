
import sys
import os
import itertools
#import pandas as pd
#import numpy as np
from ruffus import *
from statistics import mean
import subprocess
from itertools import islice

processes = 16
samtools = "samtools"

@transform(["*.bam"], suffix(".bam"), ".1_._.bed")
def bam_to_bed(infile,outfile):
    print(infile,'-->',outfile)
    cmd = f"bedtools bamtobed -i {infile} | sortBed -i - > {outfile}"
    os.system(cmd)

@follows(bam_to_bed)
@transform(["*.bam"], suffix(".bam"), ".deeptools.wg")
def bam_to_wig(infile,outfile):
    cmd = f"bamCoverage -b {infile} --outFileFormat bigwig --binSize 10 -p 16 -o {outfile}.bw"
    os.system(cmd)

    convert_bw_to_wg = f"/app/bigWigToWig {outfile}.bw {outfile}"
    os.system(convert_bw_to_wg)

@follows(bam_to_wig)
@transform(["*.deeptools.wg"], suffix(".deeptools.wg"), ".deeptools.bed")
def wig_to_bed(infile,outfile):
    print(infile,'-->',outfile)
    cmd = f"/app/wig2bed < {infile} -x > {outfile}"
    os.system(cmd)

@follows(wig_to_bed)
@transform(["*.deeptools.bed"], suffix(".deeptools.bed"), ".deeptools.filtered.bed")
def filter_wig(infile,outfile):
    print(infile, '-->', outfile)
    with open(f'{infile}', 'r+') as inputfile:
        with open(f'{outfile}', 'w+') as outputfile:
            for line in inputfile:
                line = line.strip().split("\t")
                depth = int(float(line[4]))
                if depth >=2:
                    output_data = f"{line[0]}\t{line[1]}\t{line[2]}\t{line[3]}\t{line[4]}\n"
                    outputfile.write(output_data)

@follows(filter_wig)
@transform(["*.deeptools.filtered.bed"], suffix(".deeptools.filtered.bed"), ".deeptools.merged.bed")
def merge_bed(infile,outfile):
    cmd = f"bedtools merge -i {infile} > {outfile}"
    os.system(cmd)

@follows(merge_bed)
@transform(["*.deeptools.merged.bed"], suffix(".deeptools.merged.bed"), ".2_._.bed")
def bed_to_bins(infile, outfile):
    cmd = f"bedtools makewindows -w 10 -b {infile} > {outfile}"
    os.system(cmd)

@follows(bed_to_bins)
@follows(bam_to_bed)
@collate(["*_._.bed"], formatter(r"([^/]+).([12])_._.bed$"), r"{path[0]}/{1[0]}.Summary.txt")
def summarise_bins(infiles, outfile):
    """
    1_._.bed => the bam-->bed file
    2_._.bed => the bins file
    """
    #print(infiles, '-->', outfile)
    bins_bed = str()
    sample = str()
    for i in infiles:
        if '1_._.bed' in i:
            sample = i
        else:
            bins_bed = i
    cmd = f"bedtools map -c 5,5,5 -o count,mean,collapse -a {bins_bed} -b  {sample} > {outfile}"
    os.system(cmd)

@follows(summarise_bins)
@transform(["*.Summary.txt"], suffix(".Summary.txt"), ".mapq.wig")
def create_mapq_wig(infile,outfile):
    print(infile, '-->', outfile)
    with open(f'{infile}', 'r+') as inputfile:
        with open(f'{outfile}', 'w+') as outputfile:
            for line in inputfile:
                line = line.strip().split("\t")
                chrom = line[0]
                start = line[1]
                stop  = line[2]
                depth = int(line[3])
                mapq_average = round(int(float(line[4])))
                mapq_values = line[5].split(',')
                mapq_values = (map(int, mapq_values)) # convert str to int
                total_possible_values = 60 * depth
                total_mapq_values = sum(mapq_values)
                mapq_difference = total_possible_values - total_mapq_values
                percent_variable_mapq = (mapq_difference/ total_possible_values) * depth
                mapq_transformed = (60 - mapq_average) * depth
                data = f"{chrom}\t{start}\t{stop}\t{percent_variable_mapq}\n"
                outputfile.write(data)

@follows(create_mapq_wig)
@transform(["*.mapq.wig"], suffix(".mapq.wig"), ".mapq.bw")
def wig_to_bigwig(infile,outfile):
    os.system(f"/app/wigToBigWig {infile} /app/hg19.genome {outfile}")

pipeline_run(multiprocess=int(processes))

