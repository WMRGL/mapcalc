FROM ubuntu:focal
Run apt-get update && apt-get install

# handy tip from: https://askubuntu.com/questions/909277/avoiding-user-interaction-with-tzdata-when-installing-certbo>
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt install -y wget gcc libz-dev ncurses-dev libbz2-dev liblzma-dev git \
    libcurl3-dev libcrypto++-dev make apt-utils python3.9 python3-pip bedtools rsync
RUN wget https://github.com/samtools/samtools/releases/download/1.15.1/samtools-1.15.1.tar.bz2 && \
    tar jxf samtools-1.15.1.tar.bz2 && \
    cd samtools-1.15.1 && ./configure && make install
RUN wget https://github.com/bedops/bedops/releases/download/v2.4.40/bedops_linux_x86_64-v2.4.40.tar.bz2 && \
    mkdir bedops && \
    tar jxvf bedops_linux_x86_64-v2.4.40.tar.bz2 -C bedops && cp bedops/bin/* /usr/local/bin

#RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9
RUN pip install deeptools
RUN pip install ruffus

#COPY . /app
RUN rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/linux.x86_64/bigWigToWig /app/
RUN rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/linux.x86_64/wigToBigWig /app/
RUN rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/linux.x86_64/fetchChromSizes /app/
#RUN /app/fetchChromSizes hg19 > /app/hg19.genome


RUN git clone https://github.com/WMRGL/mapcalc.git /app/mapcalc
RUN /app/fetchChromSizes hg19 > /app/hg19.genome
CMD ["python3.8", "/app/mapcalc/mapcalc.py"]
#CMD ping localhost

