RM ?= rm -f

PY_FILES := $(wildcard */*.py)
C_FILES := $(wildcard */*.c)
CXX_FILES := $(wildcard */*.cpp)
HTML_FILES := $(wildcard stage4/show*.html)
SCITE_LATEX_FILES := $(PY_FILES:%.py=%.py.scite.tex) $(C_FILES:%.c=%.c.scite.tex) \
	$(CXX_FILES:%.cpp=%.cpp.scite.tex) $(HTML_FILES:%.html=%.html.scite.tex) \
	stage4/decoded.js.scite.tex
INC_LATEX_FILES := $(SCITE_LATEX_FILES:%.scite.tex=%.inc.tex)

all: stage0/solution.bmp stage6/solution.png solution.pdf

clean:
	$(RM) solution.pdf ./*/encrypted ./*/decrypted ./*/memo.txt \
		./*/*.bin ./*/*.img ./*/*.out ./*/*.o ./*/*.pdf ./*/*.pk3 ./*/*.tar.bz2 \
		./*/*.out.* ./*/*-out.* ./*/*.inc.tex ./*/*.scite.tex \
		./*/stage*.* stage3/paint.cap stage6/congratulations.* stage*/solution.*
	$(RM) -r stage2/textures stage5/__pycache__
	latexmk -C

# SciTE LaTex export is buggy: ^ needs to be replaced with ^{ }, and other patterns too.
%.inc.tex: %.scite.tex
	sed -n '/^\\small{/,/^} %end small/p' < $< | \
	sed 's/\^/^{ }/g;s/~/~{ }/g;s/--/-{}-/g;s/\\hspace\*{1em}/\\hspace*{1.2ex}/g' > $@

# SciTE "-quit" command is buggy with Gtk+. Dirty hack to kill it once the output file is written
# FIXME: there is a race condition here!
%.scite.tex: %
	rm -f "$@"
	scite -open:$< -exportaslatex:$@ -close: -quit: & PIDSCITE=$$! && \
	while ! [ -r "$@" ] ; do sleep .5 ; done && kill $$PIDSCITE

stage0/chlg-2015:
	mkdir -p $(@D)
	wget -O $@.tmp 'http://static.sstic.org/challenge2015/chlg-2015'
	mv -f $@.tmp $@
	touch $@

stage0/solution.bmp: stage0/chlg-2015
	openssl enc -d -aes-128-ecb -in $< -out $@ -k sstic

stage1/challenge.zip:
	mkdir -p $(@D)
	wget -O $@.tmp 'http://static.sstic.org/challenge2015/challenge.zip'
	echo 'bd0df75a1d6591e01212e6e28848aec94b514e17e4ac26155696a9a76ab2ea31 $@.tmp' | sha256sum -c
	mv -f $@.tmp $@
	touch $@

stage1/sdcard.img: stage1/challenge.zip
	$(RM) $@
	cd $(@D) && unzip $(<F) $(@F)
	touch $@

stage1/inject.bin: stage1/sdcard.img
	$(RM) $@
	MTOOLS_SKIP_CHECK=1 mcopy -i $< ::$(@F) $@
	touch $@

stage1/decoded.out.txt: stage1/rubberdecode.py stage1/inject.bin
	cd $(<D) && ./$(<F) > $(@F)

stage1/stage2.zip: stage1/powerdecode.py stage1/decoded.out.txt
	cd $(<D) && ./$(<F)

stage2/stage2.zip: stage1/stage2.zip
	mkdir -p $(@D)
	echo 'ea9b8a6f5b527e72652019313c25b56ad27c7ec6 $<' | sha1sum -c
	cp -f $< $@

stage2/encrypted stage2/memo.txt stage2/sstic.pk3: stage2/stage2.zip
	$(RM) $@
	cd $(@D) && unzip $(<F) $(@F)
	touch $@

stage2/textures/sstic/%.tga: stage2/sstic.pk3
	mkdir -p $(@D)
	$(RM) $@
	cd $(<D) && unzip $(<F) $(@:$(<D)/%=%)
	touch $@

stage2/flag-green-out.png: stage2/textures/sstic/1219191984.tga
stage2/triangsig-white-out.png: stage2/textures/sstic/123771438.tga
stage2/position-orange-out.png: stage2/textures/sstic/1749623519.tga
stage2/bead-white-out.png: stage2/textures/sstic/2036414783.tga
stage2/flag-orange-out.png: stage2/textures/sstic/19281330.tga
stage2/chain-green-out.png: stage2/textures/sstic/381650771.tga
stage2/jump-green-out.png: stage2/textures/sstic/747908186.tga
stage2/monitor-white-out.png: stage2/textures/sstic/1429015180.tga

stage2/flag-tile-out.png: stage2/textures/sstic/457615433.tga
stage2/triangsig-tile-out.png: stage2/textures/sstic/1773100136.tga
stage2/position-tile-out.png: stage2/textures/sstic/1604401524.tga
stage2/bead-tile-out.png: stage2/textures/sstic/71921642.tga
stage2/chain-tile-out.png: stage2/textures/sstic/52809216.tga
stage2/jump-tile-out.png: stage2/textures/sstic/86520831.tga
stage2/monitor-tile-out.png: stage2/textures/sstic/838783866.tga

stage2/%-out.png:
	convert $< $@

stage2/decrypted: stage2/encrypted stage2/memo.txt
	sed -n 's,SHA256: \(.*\) - encrypted,\1 $<,p' stage2/memo.txt | sha256sum -c
	openssl enc -d -aes-256-ofb -in $< \
		-iv 5353544943323031352d537461676532 \
		-K 9e2f31f78153296b3d9b0ba67695dc7cb0daf152b54cdc34ffe0d35526609fac | \
		head -c -16 > $@

stage3/stage3.zip: stage2/decrypted
	sed -n 's,SHA256: \(.*\) - decrypted,\1 $<,p' stage2/memo.txt | sha256sum -c
	mkdir -p $(@D)
	cp -f $< $@

stage3/encrypted stage3/memo.txt stage3/paint.cap: stage3/stage3.zip
	$(RM) $@
	cd $(@D) && unzip $(<F) $(@F)
	touch $@

stage3/paint-out.png: stage3/decode_paint.py stage3/paint.cap
	cd $(<D) && ./$(<F)

stage3/decrypt.out: stage3/decrypt.cpp
	g++ -Wall -Wextra $< -o $@ -lcryptopp -lpthread

stage3/decrypted: stage3/decrypt.out stage3/encrypted stage3/memo.txt
	sed -n 's,SHA256: \(.*\) - encrypted,\1 stage3/encrypted,p' stage3/memo.txt | sha256sum -c
	cd $(<D) && ./$(<F)

stage4/stage4.zip: stage3/decrypted stage3/memo.txt
	sed -n 's,SHA256: \(.*\) - decrypted,\1 $<,p' stage3/memo.txt | sha256sum -c
	mkdir -p $(@D)
	cp -f $< $@

stage4/stage4.html: stage4/stage4.zip
	$(RM) $@
	cd $(@D) && unzip $(<F) $(@F)
	touch $@

stage4/stage4.out.js: stage4/stage4.html
	sed -n '/<script>/,/<\/script>/{/script>/d;p}' < $< > $@

stage4/encrypted: stage4/stage4.out.js
	sed -n 's/.*var data = "\(.*\)";.*/\1/p' $< | xxd -p -r > $@

stage4/decrypted: stage4/encrypted
	openssl enc -d -aes-128-cbc -in $< \
		-iv 4d6163696e746f73683b20496e74656c \
		-K 20582031302e363b2072763a33352e30 > $@

stage5/stage5.zip: stage4/decrypted stage4/stage4.out.js
	sed -n 's,.*var hash = "\(.*\)";.*,\1 $<,p' stage4/stage4.out.js | sha1sum -c
	mkdir -p $(@D)
	cp -f $< $@

stage5/input.bin stage5/schematic.pdf: stage5/stage5.zip
	$(RM) $@
	cd $(@D) && unzip $(<F) $(@F)
	touch $@

SECONDARY_TRANSPUTERS := 4 5 6 7 8 9 10 11 12
TRANSPUTERS_ID := 0 1 2 3
TRANSPUTERS_ID += $(addsuffix _loader, $(SECONDARY_TRANSPUTERS))
TRANSPUTERS_ID += $(addsuffix _main, $(SECONDARY_TRANSPUTERS))
TRANSPUTERS_BINFILES := $(TRANSPUTERS_ID:%=transputer%.bin)
$(TRANSPUTERS_BINFILES) stage5/input-desc-out.txt stage5/encrypted: stage5/split_input.py stage5/input.bin
	cd $(<D) && ./$(<F) > input-desc-out.txt

stage5/code-trans0-out.txt: stage5/decode_trans0.py stage5/decode_st20.py stage5/input.bin
	cd $(<D) && ./$(<F) | fmt -100 -s > $(@F)

stage5/code-trans123-out.txt: stage5/decode_trans123.py stage5/decode_st20.py stage5/input-desc-out.txt
	cd $(<D) && ./$(<F) > $(@F)

stage5/code-loader-out.txt: stage5/decode_loader.py stage5/decode_st20.py stage5/input-desc-out.txt
	cd $(<D) && ./$(<F) > $(@F)

stage5/code-all-main-out.txt: stage5/decode_all_main.py stage5/decode_st20.py stage5/input-desc-out.txt
	cd $(<D) && ./$(<F) | fmt -90 -s > $(@F)

stage5/decrypt.out: stage5/decrypt.c
	gcc -Wall -Wextra -O3 $< -o $@ -lbz2

stage5/congratulations.tar.bz2: stage5/decrypt.out stage5/encrypted
	echo 'a5790b4427bc13e4f4e9f524c684809ce96cd2f724e29d94dc999ec25e166a81 stage5/encrypted' | \
	sha256sum -c
	cd $(<D) && ./$(<F) 23517893
# Key is 0x166dac5

stage6/congratulations.tar.bz2: stage5/congratulations.tar.bz2 stage5/schematic.pdf
	echo '9128135129d2be652809f5a1d337211affad91ed5827474bf9bd7e285ecef321 $<' | \
	sha256sum -c
	mkdir -p $(@D)
	cp -f $< $@

stage6/congratulations.jpg: stage6/congratulations.tar.bz2
	cd $(<D) && tar -xjvf $(<F) $(@F)
	touch $@

stage6/hidden1.tar.bz2: stage6/congratulations.jpg
	dd if=$< of=$@ bs=1 skip=55248

stage6/congratulations.png: stage6/hidden1.tar.bz2
	cd $(<D) && tar -xjvf $(<F) $(@F)
	touch $@

stage6/hidden2.tar.bz2: stage6/extract2_from_png.py stage6/congratulations.png
	cd $(<D) && ./$(<F)

stage6/congratulations.tiff: stage6/hidden2.tar.bz2
	cd $(<D) && tar -xjvf $(<F) $(@F)
	touch $@

stage6/hidden3.tar.bz2: stage6/extract3_from_tiff.py stage6/congratulations.tiff
	cd $(<D) && ./$(<F)

stage6/congratulations.gif: stage6/hidden3.tar.bz2
	cd $(<D) && tar -xjvf $(<F) $(@F)
	touch $@

stage6/solution.png: stage6/extract4_from_gif.py stage6/congratulations.gif
	cd $(<D) && ./$(<F)

solution.pdf: $(INC_LATEX_FILES)
solution.pdf: stage2/flag-green-out.png
solution.pdf: stage2/triangsig-white-out.png
solution.pdf: stage2/position-orange-out.png
solution.pdf: stage2/bead-white-out.png
solution.pdf: stage2/flag-orange-out.png
solution.pdf: stage2/chain-green-out.png
solution.pdf: stage2/jump-green-out.png
solution.pdf: stage2/monitor-white-out.png
solution.pdf: stage2/flag-tile-out.png
solution.pdf: stage2/triangsig-tile-out.png
solution.pdf: stage2/position-tile-out.png
solution.pdf: stage2/bead-tile-out.png
solution.pdf: stage2/chain-tile-out.png
solution.pdf: stage2/jump-tile-out.png
solution.pdf: stage2/monitor-tile-out.png
solution.pdf: stage3/paint-out.png
solution.pdf: stage5/input-desc-out.txt
solution.pdf: stage5/code-trans0-out.txt
solution.pdf: stage5/code-trans123-out.txt
solution.pdf: stage5/code-loader-out.txt
solution.pdf: stage5/code-all-main-out.txt

solution.pdf: solution.tex
	latexmk -pdf < /dev/null

.PHONY: clean all
.PRECIOUS: stage2/textures/sstic/%.tga %.inc.tex %.scite.tex
