# $Id: setup.py,v 1.13 2009/04/25 22:49:33 asc Exp $

# http://peak.telecommunity.com/DevCenter/setuptools
# http://ianbicking.org/docs/setuptools-presentation/

try:
    from setuptools import setup, find_packages
except:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

readme = file('README','rb').read()

local__name = 'clusterMMap'
local__version = '0.1'
local__url = 'http://www.aaronland.info/python/%s' % local__name
local__download = '%s/%s-%s.tar.gz' % (local__url, local__name, local__version)

setup(
    name = local__name,
    version = local__version,

    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    exclude_package_data={'':["examples", "README", "ez_setup*"]},

    install_requires = ['shapely', 'cluster', 'numpy'],
    dependency_links = ['http://bonsai.ims.u-tokyo.ac.jp/~mdehoon/software/cluster/software.htm'],

    author = "Aaron Straup Cope",
    author_email = "aaron@aaronland.net",
    description = "Generate a set of clusters and orphaned points for a list of coordinates",
    long_description=readme,
    
    license = "BSD",
    keywords = "cluster kmeans",
    url = local__url,
    download_url = local__download,
    
    # Uncomment when you need to sanity check the
    # stuff that actually gets installed...
    zip_safe=False    
    )
