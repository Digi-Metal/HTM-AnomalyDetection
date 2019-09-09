# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 14:02:11 2019

@author: Ming Jin
"""

import copy

from nupic.data.field_meta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial
from nupic.data.record_stream import RecordStreamIface
from nupic.data.utils import (intOrNone, floatOrNone, parseBool, parseTimestamp,
    serializeTimestamp, serializeTimestampNoMS, escape, unescape, parseSdr,
    serializeSdr, parseStringList, stripList)


class streamReader(RecordStreamIface):

  def __init__(self, streamID, names, types, specials):
    super(streamReader, self).__init__()
    
    self.names = names
    self.types = types
    self.specials = specials

    self._filename = streamID
    self._file = open(self._filename, 'r')
    self._sequences = set()
    self.rewindAtEOF = False

#    self._reader = file.reader(self._file)

    self._fields = [FieldMetaInfo(*attrs)
                    for attrs in zip(self.names, self.types, self.specials)]
    
    self._fieldCount = len(self._fields)

    # Keep track on how many records have been read/written
    self._recordCount = 0

    self._timeStampIdx = (self.specials.index(FieldMetaSpecial.timestamp)
                          if FieldMetaSpecial.timestamp in self.specials else None)
    self._resetIdx = (self.specials.index(FieldMetaSpecial.reset)
                      if FieldMetaSpecial.reset in self.specials else None)
    self._sequenceIdIdx = (self.specials.index(FieldMetaSpecial.sequence)
                           if FieldMetaSpecial.sequence in self.specials else None)
    self._categoryIdx = (self.specials.index(FieldMetaSpecial.category)
                         if FieldMetaSpecial.category in self.specials else None)
    self._learningIdx = (self.specials.index(FieldMetaSpecial.learning)
                         if FieldMetaSpecial.learning in self.specials else None)

    # keep track of the current sequence
    self._currSequence = None
    self._currTime = None

    if self._timeStampIdx:
      assert self.types[self._timeStampIdx] == FieldMetaType.datetime
    if self._sequenceIdIdx:
      assert self.types[self._sequenceIdIdx] in (FieldMetaType.string,
                                            FieldMetaType.integer)
    if self._resetIdx:
      assert self.types[self._resetIdx] == FieldMetaType.integer
    if self._categoryIdx:
      assert self.types[self._categoryIdx] in (FieldMetaType.list,
                                          FieldMetaType.integer)
    if self._learningIdx:
      assert self.types[self._learningIdx] == FieldMetaType.integer

    # Convert the types to the actual types in order to convert the strings
    m = {FieldMetaType.integer: intOrNone,
        FieldMetaType.float: floatOrNone,
        FieldMetaType.boolean: parseBool,
        FieldMetaType.string: unescape,
        FieldMetaType.datetime: parseTimestamp,
        FieldMetaType.sdr: parseSdr,
        FieldMetaType.list: parseStringList}
 
    self._adapters = [m[t] for t in self.types]

    # Dictionary to store record statistics (min and max of scalars for now)
    self._stats = None

  '''
  methods that not implement
  '''
  def appendRecord(self):
    return None

  def appendRecords(self):
    return None

  def clearStats(self):
    return None

  def flush(self):
    return None

  def getBookmark(self):
    return None

  def getError(self):
    return None

  def getStats(self):
    return None

  def isCompleted(self):
    return None

  def recordsExistAfter(self):
    return None

  def seekFromEnd(self):
    return None

  def setCompleted(self):
    return None

  def setError(self):
    return None

  def setTimeout(self):
    return None

  def close(self):
    return None

  def __getstate__(self):
    return None

  def __setstate__(self):
    return None

  def rewind(self):
    return None

  def setAutoRewind(self):
    return None

  def _updateSequenceInfo(self, r):
    return None


  '''
  The methods have been implemented
  '''

  def getFieldNames(self):
    """
    returns: (list) field names associated with the data.
    """
    return [f.name for f in self._fields]


  def getFields(self):
    """
    returns: a sequence of :class:`~.FieldMetaInfo`
              ``name``/``type``/``special`` tuples for each field in the stream.
    """
    if self._fields is None:
      return None
    else:
      return copy.copy(self._fields)


  def getNextRecord(self, useCache=True):
    """ Returns next available data record from the file.

    returns: a data row (a list or tuple) if available; None, if no more
              records in the table (End of Stream - EOS); empty sequence (list
              or tuple) when timing out while waiting for the next record.
    """
    assert self._file is not None

    # Read the line
    try:
      line = self._file.readline().strip()
      lines = line.split(', ')
    except:
      raise StopIteration
      
    self._recordCount += 1
    record = []
    for i, f in enumerate(lines):
        record.append(self._adapters[i](f))

    return record


  def getNextRecordIdx(self):
    """
    returns: (int) the index of the record that will be read next from
              :meth:`~.FileRecordStream.getNextRecord`.
    """
    return self._recordCount


  def __enter__(self):
    """Context guard - enter

    Just return the object
    """
    return self


  def __exit__(self, yupe, value, traceback):
    """Context guard - exit

    Ensures that the file is always closed at the end of the 'with' block.
    Lets exceptions propagate.
    """
    self.close()


  def __iter__(self):
    """Support for the iterator protocol. Return itself"""
    return self


  def next(self):
    """Implement the iterator protocol """
    record = self.getNextRecord()
    if record is None:
      raise StopIteration

    return record
