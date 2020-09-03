build_rpm:
	python3 setup.py bdist_rpm

install:
	dnf -y reinstall dist/repoman-*.noarch.rpm

clean:
	rm -r dist/
	
