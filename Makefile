build_rpm:
	python3 setup.py bdist_rpm

install:
	dnf -y install dist/repoman-*.noarch.rpm

clean:
	rm -r dist/
	
