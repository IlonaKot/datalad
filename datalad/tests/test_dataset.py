# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Test implementation of class Dataset

Note: There's not a lot to test by now.

"""

import os.path
import platform

from nose.tools import assert_raises, assert_is_instance, assert_true, assert_equal, assert_false
from git.exc import GitCommandError

from datalad.support.dataset import Dataset
from datalad.tests.utils import with_tempfile, with_testrepos, assert_cwd_unchanged, ignore_nose_capturing_stdout, \
    on_windows, ok_clean_git, ok_clean_git_annex_proxy


# For now (at least) we would need to clone from the network
# since there are troubles with submodules on Windows.
# See: https://github.com/datalad/datalad/issues/44
local_flavors = ['network-clone' if on_windows else 'local']

@ignore_nose_capturing_stdout
@assert_cwd_unchanged
@with_testrepos(flavors=local_flavors)
@with_tempfile
def test_Dataset(src, dst):

    ds = Dataset(dst, src)
    assert_is_instance(ds, Dataset, "Dataset was not created.")
    assert_true(os.path.exists(os.path.join(dst, '.datalad')))

    #do it again should raise GitCommandError since git will notice there's already a git-repo at that path
    assert_raises(GitCommandError, Dataset, dst, src)

@ignore_nose_capturing_stdout
@assert_cwd_unchanged
@with_testrepos(flavors=local_flavors)
@with_tempfile
def test_Dataset_direct(src, dst):

    ds = Dataset(dst, src, direct=True)
    assert_is_instance(ds, Dataset, "Dataset was not created.")
    assert_true(os.path.exists(os.path.join(dst, '.datalad')))
    assert_true(ds.is_direct_mode(), "Forcing direct mode failed.")
    

@ignore_nose_capturing_stdout
@assert_cwd_unchanged
@with_testrepos(flavors=local_flavors)
def test_Dataset_instance_from_existing(path):

    gr = Dataset(path)
    assert_is_instance(gr, Dataset, "Dataset was not created.")
    assert_true(os.path.exists(os.path.join(path, '.datalad')))


@ignore_nose_capturing_stdout
@assert_cwd_unchanged
@with_tempfile
def test_Dataset_instance_brand_new(path):

    gr = Dataset(path)
    assert_is_instance(gr, Dataset, "Dataset was not created.")
    assert_true(os.path.exists(os.path.join(path, '.datalad')))


@ignore_nose_capturing_stdout
@with_testrepos(flavors=['network'])
@with_tempfile
def test_Dataset_get(src, dst):

    ds = Dataset(dst, src)
    assert_is_instance(ds, Dataset, "AnnexRepo was not created.")

    cwd = os.getcwd()
    os.chdir(dst)
    testfile = 'test-annex.dat'
    if platform.system() != "Windows":
        assert_raises(IOError, open, testfile, 'r')
        # If get has nothing to do, we can't test it.
        # TODO: see test_AnnexRepo_get()

    ds.get([testfile])
    f = open(testfile, 'r')
    assert_equal(f.readlines(), ['123\n'], "test-annex.dat's content doesn't match.")

    os.chdir(cwd)


@assert_cwd_unchanged
@with_testrepos(flavors=local_flavors)
@with_tempfile
def test_Dataset_add_to_annex(src, dst):

    ds = Dataset(dst, src)
    filename = 'file_to_annex.dat'
    filename_abs = os.path.join(dst, filename)
    f = open(filename_abs, 'w')
    f.write("What to write?")
    f.close()
    cwd = os.getcwd()
    os.chdir(dst)
    ds.add_to_annex([filename])
    os.chdir(cwd)

    if not ds.is_direct_mode():
        assert_true(os.path.islink(filename_abs), "Annexed file is not a link.")
        ok_clean_git(dst, annex=True)
    else:
        assert_false(os.path.islink(filename_abs), "Annexed file is link in direct mode.")
        # TODO: How to test the file was added in direct mode?
        # May be this will need 'git annex find' or sth. to be implemented.
        ok_clean_git_annex_proxy(dst)


@assert_cwd_unchanged
@with_testrepos(flavors=local_flavors)
@with_tempfile
def test_Dataset__add_to_git(src, dst):

    ds = Dataset(dst, src)
    filename = 'file_to_git.dat'
    filename_abs = os.path.join(dst, filename)
    f = open(filename_abs, 'w')
    f.write("What to write?")
    f.close()
    ds.add_to_git([filename])
    if ds.is_direct_mode():
        ok_clean_git_annex_proxy(dst)
    else:
        ok_clean_git(dst, annex=False)


@assert_cwd_unchanged
@with_tempfile
def test_Dataset_commit(path):

    ds = Dataset(path)
    filename = os.path.join(path, "test_git_add.dat")
    f = open(filename, 'w')
    f.write("File to add to git")
    f.close()
    cwd = os.getcwd()
    os.chdir(path)
    ds.annex_add([filename])
    os.chdir(cwd)

    if ds.is_direct_mode():
        assert_raises(AssertionError, ok_clean_git_annex_proxy, path)
    else:
        assert_raises(AssertionError, ok_clean_git, path, annex=True)

    ds._commit("test _commit")

    if ds.is_direct_mode():
        ok_clean_git_annex_proxy(path)
    else:
        ok_clean_git(path, annex=True)