# (C) British Crown Copyright 2013 - 2014, Met Office
#
# This file is part of Iris.
#
# Iris is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Iris is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Iris.  If not, see <http://www.gnu.org/licenses/>.


# import iris tests first so that some things can be initialised before importing anything else
import iris.tests as tests

from copy import deepcopy
import os
from types import GeneratorType
import unittest

import biggus
import netcdftime

import iris.fileformats
import iris.fileformats.pp as pp
import iris.util


@tests.skip_data
class TestPPCopy(tests.IrisTest):
    def setUp(self):
        self.filename = tests.get_data_path(('PP', 'aPPglob1', 'global.pp'))

    def test_copy_field_deferred(self):
        field = pp.load(self.filename).next()
        clone = field.copy()
        self.assertIsInstance(clone._data, biggus.Array)
        self.assertEqual(field, clone)
        clone.lbyr = 666
        self.assertNotEqual(field, clone)

    def test_deepcopy_field_deferred(self):
        field = pp.load(self.filename).next()
        clone = deepcopy(field)
        self.assertIsInstance(clone._data, biggus.Array)
        self.assertEqual(field, clone)
        clone.lbyr = 666
        self.assertNotEqual(field, clone)

    def test_copy_field_non_deferred(self):
        field = pp.load(self.filename, True).next()
        clone = field.copy()
        self.assertEqual(field, clone)
        clone.data[0][0] = 666
        self.assertNotEqual(field, clone)

    def test_deepcopy_field_non_deferred(self):
        field = pp.load(self.filename, True).next()
        clone = deepcopy(field)
        self.assertEqual(field, clone)
        clone.data[0][0] = 666
        self.assertNotEqual(field, clone)


class IrisPPTest(tests.IrisTest):
    def check_pp(self, pp_fields, reference_filename):
        """
        Checks the given iterable of PPField objects matches the reference file, or creates the
        reference file if it doesn't exist.

        """
        # turn the generator into a list 
        pp_fields = list(pp_fields)
        
        # Load deferred data for all of the fields (but don't do anything with it)
        for pp_field in pp_fields:
            pp_field.data
            
        test_string = str(pp_fields)
        reference_path = tests.get_result_path(reference_filename)
        if os.path.isfile(reference_path):
            reference = ''.join(open(reference_path, 'r').readlines())
            self._assert_str_same(reference+'\n', test_string+'\n', reference_filename, type_comparison_name='PP files')
        else:
            tests.logger.warning('Creating result file: %s', reference_path)
            open(reference_path, 'w').writelines(test_string)


class TestPPHeaderDerived(unittest.TestCase):

    def setUp(self):
        self.pp = pp.PPField2()
        self.pp.lbuser = (0, 1, 2, 3, 4, 5, 6)
        self.pp.lbtim = 11
        self.pp.lbproc = 65539

    def test_standard_access(self):
        self.assertEqual(self.pp.lbtim, 11)
        
    def test_lbtim_access(self):
        self.assertEqual(self.pp.lbtim[0], 1)
        self.assertEqual(self.pp.lbtim.ic, 1)
        
    def test_lbtim_setter(self):
        self.pp.lbtim[4] = 4
        self.pp.lbtim[0] = 4
        self.assertEqual(self.pp.lbtim[0], 4)
        self.assertEqual(self.pp.lbtim.ic, 4)
        
        self.pp.lbtim.ib = 9
        self.assertEqual(self.pp.lbtim.ib, 9)
        self.assertEqual(self.pp.lbtim[1], 9)
        
    def test_lbproc_access(self):
        # lbproc == 65539
        self.assertEqual(self.pp.lbproc[0], 9)
        self.assertEqual(self.pp.lbproc[19], 0)
        self.assertEqual(self.pp.lbproc.flag1, 1)
        self.assertEqual(self.pp.lbproc.flag65536, 1)
        self.assertEqual(self.pp.lbproc.flag131072, 0)
    
    def test_set_lbuser(self):
        self.pp.stash = 'm02s12i003'
        self.assertEqual(self.pp.stash, pp.STASH(2, 12, 3))
        self.pp.lbuser[6] = 5
        self.assertEqual(self.pp.stash, pp.STASH(5, 12, 3))
        self.pp.lbuser[3] = 4321
        self.assertEqual(self.pp.stash, pp.STASH(5, 4, 321))
    
    def test_set_stash(self):
        self.pp.stash = 'm02s12i003'
        self.assertEqual(self.pp.stash, pp.STASH(2, 12, 3))

        self.pp.stash = pp.STASH(3, 13, 4)
        self.assertEqual(self.pp.stash, pp.STASH(3, 13, 4))
        self.assertEqual(self.pp.lbuser[3], self.pp.stash.lbuser3())
        self.assertEqual(self.pp.lbuser[6], self.pp.stash.lbuser6())
        
        with self.assertRaises(ValueError):
            self.pp.stash = (4, 15, 5)
        
    def test_lbproc_bad_access(self):
        try:
            print self.pp.lbproc.flag65537
        except AttributeError:
            pass
        except Exception as err:
            self.fail("Should return a better error: " + str(err))


@tests.skip_data
class TestPPField_GlobalTemperature(IrisPPTest):
    def setUp(self):
        self.original_pp_filepath = tests.get_data_path(('PP', 'aPPglob1', 'global.pp'))
        self.r = list(pp.load(self.original_pp_filepath))

    def test_full_file(self):
        self.check_pp(self.r[0:10], ('PP', 'global_test.pp.txt'))   
            
    def test_lbtim_access(self):
        self.assertEqual(self.r[0].lbtim[0], 2)
        self.assertEqual(self.r[0].lbtim.ic, 2)
    
    def test_lbproc_access(self):
        self.assertEqual(self.r[0].lbproc[0], 8)
        self.assertEqual(self.r[0].lbproc[19], 0)
        self.assertEqual(self.r[0].lbproc.flag1, 0)
        self.assertEqual(self.r[0].lbproc.flag65536, 0)
        self.assertEqual(self.r[0].lbproc.flag131072, 0)

    def test_t1_t2_access(self):
        self.assertEqual(self.r[0].t1.timetuple(), netcdftime.datetime(1994, 12, 1, 0, 0).timetuple())

    def test_save_single(self):
        temp_filename = iris.util.create_temp_filename(".pp")
        self.r[0].save(open(temp_filename, 'wb'))
        self.assertEqual(self.file_checksum(temp_filename), self.file_checksum(self.original_pp_filepath))
        os.remove(temp_filename)
           
    def test_save_api(self):
        filepath = self.original_pp_filepath
        
        f = pp.load(filepath).next()

        temp_filename = iris.util.create_temp_filename(".pp")
        
        f.save(open(temp_filename, 'wb'))
        self.assertEqual(self.file_checksum(temp_filename), self.file_checksum(filepath))
        
        os.remove(temp_filename)
    

@tests.skip_data
class TestPackedPP(IrisPPTest):
    def test_wgdos(self):
        r = pp.load(tests.get_data_path(('PP', 'wgdos_packed', 'nae.20100104-06_0001.pp')))
        
        # Check that the result is a generator and convert to a list so that we can index and get the first one
        self.assertEqual( type(r), GeneratorType)
        r = list(r)
        
        self.check_pp(r, ('PP', 'nae_unpacked.pp.txt'))
        
        # check that trying to save this field again raises an error (we cannot currently write WGDOS packed fields)
        temp_filename = iris.util.create_temp_filename(".pp")
        self.assertRaises(NotImplementedError, r[0].save, open(temp_filename, 'wb'))
        os.remove(temp_filename)
        
    def test_rle(self):
        r = pp.load(tests.get_data_path(('PP', 'ocean_rle', 'ocean_rle.pp')))

        # Check that the result is a generator and convert to a list so that we can index and get the first one
        self.assertEqual( type(r), GeneratorType)
        r = list(r)

        self.check_pp(r, ('PP', 'rle_unpacked.pp.txt'))

        # check that trying to save this field again raises an error
        # (we cannot currently write RLE packed fields)
        with self.temp_filename('.pp') as temp_filename:
            with self.assertRaises(NotImplementedError):
                r[0].save(open(temp_filename, 'wb'))


@tests.skip_data
class TestPPFile(IrisPPTest):
    def test_lots_of_extra_data(self):
        r = pp.load(tests.get_data_path(('PP', 'cf_processing', 'HadCM2_ts_SAT_ann_18602100.b.pp')))
        r = list(r)
        self.assertEqual(r[0].lbcode.ix, 13)
        self.assertEqual(r[0].lbcode.iy, 23)
        self.assertEqual(len(r[0].lbcode), 5)
        self.check_pp(r, ('PP', 'extra_data_time_series.pp.txt'))
        

@tests.skip_data
class TestPPFileExtraXData(IrisPPTest):
    def setUp(self):
        self.original_pp_filepath = tests.get_data_path(('PP', 'ukV1', 'ukVpmslont.pp'))
        self.r = list(pp.load(self.original_pp_filepath))[0:5]
        
    def test_full_file(self):
        self.check_pp(self.r, ('PP', 'extra_x_data.pp.txt'))

    def test_save_single(self):
        filepath = tests.get_data_path(('PP', 'ukV1', 'ukVpmslont_first_field.pp'))
        f = pp.load(filepath).next()

        temp_filename = iris.util.create_temp_filename(".pp")
        f.save(open(temp_filename, 'wb'))
        
        s = pp.load(temp_filename).next()
        
        # force the data to be loaded (this was done for f when save was run)
        s.data
        self._assert_str_same(str(s)+'\n', str(f)+'\n', '', type_comparison_name='PP files')
        
        self.assertEqual(self.file_checksum(temp_filename), self.file_checksum(filepath))
        os.remove(temp_filename)
    

@tests.skip_data
class TestPPFileWithExtraCharacterData(IrisPPTest):
    def setUp(self):
        self.original_pp_filepath = tests.get_data_path(('PP', 'globClim1', 'dec_subset.pp'))
        self.r = pp.load(self.original_pp_filepath)
        self.r_loaded_data = pp.load(self.original_pp_filepath, read_data=True)
        
        # Check that the result is a generator and convert to a list so that we can index and get the first one
        self.assertEqual( type(self.r), GeneratorType)
        self.r = list(self.r)
        
        self.assertEqual( type(self.r_loaded_data), GeneratorType)
        self.r_loaded_data = list(self.r_loaded_data)
        
            
    def test_extra_field_title(self):
        self.assertEqual(self.r[0].field_title, 'AJHQA Time mean  !C Atmos u compnt of wind after timestep at 9.998 metres !C 01/12/2007 00:00 -> 01/01/2008 00:00')    

    def test_full_file(self):
        self.check_pp(self.r[0:10], ('PP', 'extra_char_data.pp.txt'))
        self.check_pp(self.r_loaded_data[0:10], ('PP', 'extra_char_data.w_data_loaded.pp.txt'))   
    
    def test_save_single(self):
        filepath = tests.get_data_path(('PP', 'model_comp', 'dec_first_field.pp'))
        f = pp.load(filepath).next()

        temp_filename = iris.util.create_temp_filename(".pp")
        f.save(open(temp_filename, 'wb'))
        
        s = pp.load(temp_filename).next()
        
        # force the data to be loaded (this was done for f when save was run)
        s.data
        self._assert_str_same(str(s)+'\n', str(f)+'\n', '', type_comparison_name='PP files')
        
        self.assertEqual(self.file_checksum(temp_filename), self.file_checksum(filepath))
        os.remove(temp_filename)
    

class TestBitwiseInt(unittest.TestCase):

    def test_3(self):
        t = pp.BitwiseInt(3)
        self.assertEqual(t[0], 3)
        self.assertTrue(t.flag1)
        self.assertTrue(t.flag2)
        self.assertRaises(AttributeError, getattr, t, "flag1024")
        
    def test_setting_flags(self):
        t = pp.BitwiseInt(3)
        self.assertEqual(t._value, 3)

        t.flag1 = False
        self.assertEqual(t._value, 2)
        t.flag2 = False
        self.assertEqual(t._value, 0)
        
        t.flag1 = True
        self.assertEqual(t._value, 1)
        t.flag2 = True
        self.assertEqual(t._value, 3)
        
        self.assertRaises(AttributeError, setattr, t, "flag1024", True)
        self.assertRaises(TypeError, setattr, t, "flag2", 1)

        t = pp.BitwiseInt(3, num_bits=11)
        t.flag1024 = True
        self.assertEqual(t._value, 1027)

    def test_standard_operators(self):
        t = pp.BitwiseInt(323)
        
        self.assertTrue(t == 323)
        self.assertFalse(t == 324)
        
        self.assertFalse(t != 323)
        self.assertTrue(t != 324)
        
        self.assertTrue(t >= 323)
        self.assertFalse(t >= 324)
        
        self.assertFalse(t > 323)
        self.assertTrue(t > 322)
        
        self.assertTrue(t <= 323)
        self.assertFalse(t <= 322)
        
        self.assertFalse(t < 323)
        self.assertTrue(t < 324)

        self.assertTrue(t in [323])
        self.assertFalse(t in [324])

    def test_323(self):
        t = pp.BitwiseInt(323)
        self.assertRaises(AttributeError, getattr, t, 'flag0')
        
        self.assertEqual(t.flag1, 1)
        self.assertEqual(t.flag2, 1)
        self.assertEqual(t.flag4, 0)
        self.assertEqual(t.flag8, 0)
        self.assertEqual(t.flag16, 0)
        self.assertEqual(t.flag32, 0)
        self.assertEqual(t.flag64, 1)
        self.assertEqual(t.flag128, 0)
        self.assertEqual(t.flag256, 1)


    def test_33214(self):
        t = pp.BitwiseInt(33214)
        self.assertEqual(t[0], 4)
        self.assertEqual(t.flag1, 0)
        self.assertEqual(t.flag2, 1)

    def test_negative_number(self):
        try:
            _ = pp.BitwiseInt(-5)
        except ValueError as err:
            self.assertEqual(str(err), 'Negative numbers not supported with splittable integers object')

    def test_128(self):
        t = pp.BitwiseInt(128)
        self.assertEqual(t.flag1, 0)
        self.assertEqual(t.flag2, 0)
        self.assertEqual(t.flag4, 0)
        self.assertEqual(t.flag8, 0)
        self.assertEqual(t.flag16, 0)
        self.assertEqual(t.flag32, 0)
        self.assertEqual(t.flag64, 0)
        self.assertEqual(t.flag128, 1)
        

class TestSplittableInt(unittest.TestCase):

    def test_3(self):
        t = pp.SplittableInt(3)
        self.assertEqual(t[0], 3)
        
    def test_grow_str_list(self):
        t = pp.SplittableInt(3)
        t[1] = 3
        self.assertEqual(t[1], 3)
        
        t[5] = 4
        
        self.assertEqual(t[5], 4)
        
        self.assertEqual( int(t), 400033)
        
        self.assertEqual(t, 400033)
        self.assertNotEqual(t, 33)
        
        self.assertTrue(t >= 400033)
        self.assertFalse(t >= 400034)
        
        self.assertTrue(t <= 400033)
        self.assertFalse(t <= 400032)
        
        self.assertTrue(t > 400032)
        self.assertFalse(t > 400034)
        
        self.assertTrue(t < 400034)
        self.assertFalse(t < 400032)        

    def test_name_mapping(self):
        t = pp.SplittableInt(33214, {'ones':0, 'tens':1, 'hundreds':2})
        self.assertEqual(t.ones, 4)
        self.assertEqual(t.tens, 1)
        self.assertEqual(t.hundreds, 2)
        
        t.ones = 9
        t.tens = 4
        t.hundreds = 0
        
        self.assertEqual(t.ones, 9)
        self.assertEqual(t.tens, 4)
        self.assertEqual(t.hundreds, 0)
        
    def test_name_mapping_multi_index(self):
        t = pp.SplittableInt(33214, {'weird_number':slice(None, None, 2), 
                                     'last_few':slice(-2, -5, -2), 
                                     'backwards':slice(None, None, -1)})
        self.assertEqual(t.weird_number, 324)
        self.assertEqual(t.last_few, 13)
        self.assertRaises(ValueError, setattr, t, 'backwards', 1)
        self.assertRaises(ValueError, setattr, t, 'last_few', 1)
        self.assertEqual(t.backwards, 41233)
        self.assertEqual(t, 33214)
        
        t.weird_number = 99
        # notice that this will zero the 5th number
        
        self.assertEqual(t, 3919)
        t.weird_number = 7899
        self.assertEqual(t, 7083919)
        t.foo = 1
        
        t = pp.SplittableInt(33214, {'ix':slice(None, 2), 'iy':slice(2, 4)})
        self.assertEqual(t.ix, 14)
        self.assertEqual(t.iy, 32)
        
        t.ix = 21
        self.assertEqual(t, 33221)
        
        t = pp.SplittableInt(33214, {'ix':slice(-1, 2)})
        self.assertEqual(t.ix, 0)

        t = pp.SplittableInt(4, {'ix':slice(None, 2), 'iy':slice(2, 4)})
        self.assertEqual(t.ix, 4)
        self.assertEqual(t.iy, 0)
        
    def test_33214(self):
        t = pp.SplittableInt(33214)
        self.assertEqual(t[4], 3)
        self.assertEqual(t[3], 3)
        self.assertEqual(t[2], 2)
        self.assertEqual(t[1], 1)
        self.assertEqual(t[0], 4)
        
        # The rest should be zero
        for i in range(5, 100):
            self.assertEqual(t[i], 0)

    def test_negative_number(self):
        self.assertRaises(ValueError, pp.SplittableInt, -5)
        try:
            _ = pp.SplittableInt(-5)
        except ValueError as err:
            self.assertEqual(str(err), 'Negative numbers not supported with splittable integers object')

            
class TestSplittableIntEquality(unittest.TestCase):
    def test_not_implemented(self):
        class Terry(object): pass
        sin = pp.SplittableInt(0)
        self.assertIs(sin.__eq__(Terry()), NotImplemented)
        self.assertIs(sin.__ne__(Terry()), NotImplemented)


class TestPPDataProxyEquality(unittest.TestCase):
    def test_not_implemented(self):
        class Terry(object): pass
        pox = pp.PPDataProxy("john", "michael", "eric", "graham", "brian",
                             "spam", "beans", "eggs")
        self.assertIs(pox.__eq__(Terry()), NotImplemented)
        self.assertIs(pox.__ne__(Terry()), NotImplemented)


class TestPPFieldEquality(unittest.TestCase):
    def test_not_implemented(self):
        class Terry(object): pass
        pox = pp.PPField3()
        self.assertIs(pox.__eq__(Terry()), NotImplemented)
        self.assertIs(pox.__ne__(Terry()), NotImplemented)


if __name__ == "__main__":
    tests.main()
