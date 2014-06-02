# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from dirigible.sheet.utils.cell_name_utils import coordinates_to_cell_name



class CellRange(object):

    def __init__(self, worksheet, start, end):
        self.worksheet = worksheet
        self.left, self.right = sorted([start[0], end[0]])
        self.top, self.bottom =  sorted([start[1], end[1]])


    def __repr__(self):
        return '<CellRange %s to %s in %s>' % (
            coordinates_to_cell_name(self.left, self.top),
            coordinates_to_cell_name(self.right, self.bottom),
            str(self.worksheet)
        )


    def __eq__(self, other):
        return (
            isinstance(other, CellRange) and
            self.worksheet == other.worksheet and
            self.left == other.left and
            self.right == other.right and
            self.top == other.top and
            self.bottom == other.bottom
        )


    def __ne__(self, other):
        return not self.__eq__(other)


    def __len__(self):
        return (self.right - self.left + 1) * (self.bottom - self.top + 1)


    @property
    def locations(self):
        for r in xrange(self.top, self.bottom + 1):
            for c in xrange(self.left, self.right + 1):
                yield c, r


    def __iter__(self):
        for location in self.locations:
            yield self.worksheet[location].value


    @property
    def cells(self):
        for loc in self.locations:
            yield self.worksheet[loc]


    @property
    def locations_and_cells(self):
        for loc in self.locations:
            yield loc, self.worksheet[loc]


    def _location_in_worksheet(self, location):
        if 0 in location:
            raise IndexError('Cell ranges are 1-indexed')
        num_cols = self.right - self.left + 1
        num_rows = self.bottom - self.top + 1

        if abs(location[0]) > num_cols:
            raise IndexError('Cell range only has %s columns' % (num_cols, ))
        elif abs(location[1]) > num_rows:
            raise IndexError('Cell range only has %s rows' % (num_rows, ))
        else:
            return location[0] + self.left - 1, location[1] + self.top - 1


    def __getitem__(self, location):
            return self.worksheet[self._location_in_worksheet(location)]


    def __setitem__(self, location, value):
        self.worksheet[self._location_in_worksheet(location)] = value


    def clear(self):
        for cell in self.cells:
            cell.clear()
