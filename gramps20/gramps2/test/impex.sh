#! /bin/sh
#
# Import/export test for GRAMPS: Import example XML data and create GRDB,
# check data for integrity, output in all formats, check resulting XML for
# well-formedness and validate it against DTD and RelaxNG schema.

# $Id$

TOP_DIR=`dirname $PWD`
TEST_DIR=$TOP_DIR/test
SRC_DIR=$TOP_DIR/src
PRG="python gramps.py"
EXAMPLE_XML=$TOP_DIR/example/gramps/example.gramps

OUT_FMT="gedcom gramps-xml gramps-pkg wft geneweb"
DATA_DIR=$TEST_DIR/data
mkdir -p $DATA_DIR
if [ -f $DATA_DIR/example.grdb ]; then
    rm $DATA_DIR/example.grdb
fi

echo ""
echo "+--------------------------------------------------------------"
echo "| Import XML, write GRDB"
echo "+--------------------------------------------------------------"
OPTS="-i $EXAMPLE_XML -o $DATA_DIR/example.grdb"
(cd $SRC_DIR; $PRG $OPTS)

echo ""
echo "+--------------------------------------------------------------"
echo "| Check GRDB for errors"
echo "+--------------------------------------------------------------"
OPTS="-O $DATA_DIR/example.grdb -a tool -p name=check"
(cd $SRC_DIR; $PRG $OPTS)

echo ""
echo "+--------------------------------------------------------------"
echo "| Open GRDB, write all other formats"
echo "+--------------------------------------------------------------"
OPTS="-O $DATA_DIR/example.grdb"
for fmt in $OUT_FMT; do
    OPTS="$OPTS -o $DATA_DIR/example.$fmt -f $fmt"
done
(cd $SRC_DIR; $PRG $OPTS)

echo ""
echo "+--------------------------------------------------------------"
echo "| Validate produced XML"
echo "+--------------------------------------------------------------"
echo "* Regular well-formedness and DTD validation"
xmllint --noout --valid $DATA_DIR/example.gramps-xml
echo "* Post-parsing DTD validation"
xmllint --noout --postvalid $DATA_DIR/example.gramps-xml
echo "* Validate against RelaxNG schema"
xmllint --noout --relaxng $TOP_DIR/doc/grampsxml.rng $DATA_DIR/example.gramps-xml
