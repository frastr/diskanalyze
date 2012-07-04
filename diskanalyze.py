#----------------------------------------------------------------------
# Disk usage analyzer with save information into sqlite database
#----------------------------------------------------------------------
import sys
import os
import os.path
import string
import sqlite3


#----------------------------------------------------------------------
# Recursive function for the determination disk usage
#----------------------------------------------------------------------
def analyzeDir( conn, directory):

	size = os.path.getsize( directory)
	size_total = size
	conn.execute( "insert into files ( type, path, size) values ( 'D', '%s', %d)" \
		% ( directory.replace( "'", "''"), size))

	for filename in os.listdir( directory):
		fullname = os.path.join( directory, filename)

		if os.path.islink( fullname):
			size = len( os.readlink( fullname))
			size_total += size
			conn.execute( "insert into files ( type, path, filename, size) values ( 'L', '%s', '%s', %d)" \
				% ( directory.replace( "'", "''"), filename.replace( "'", "''"), size))
			continue

		if os.path.isdir( fullname):
			size_total += analyzeDir( conn, fullname)
			continue

		size = os.path.getsize( fullname);
		size_total += size

		conn.execute( "insert into files ( type, path, filename, size) values ( 'F', '%s', '%s', %d)" \
			% ( directory.replace( "'", "''"), filename.replace( "'", "''"), size))

	# directory summary
	conn.execute( "insert into summary ( path, level, size) values ( '%s', %d, %d)" \
		% ( directory.replace( "'", "''"), directory.count( os.path.sep), size_total))

	return size_total


#----------------------------------------------------------------------
# Human-readable output of size
#----------------------------------------------------------------------
def HumanSize( size):
	if size > ( 1024 * 1024 * 1024):
		return ( size / 1024.0 / 1024.0 / 1024.0, 'GB')
	elif size > ( 1024 * 1024):
		return ( size / 1024.0 / 1024.0, 'MB')
	elif size > 1024:
		return ( size / 1024.0, 'KB')
	else:
		return ( size, 'B')


#----------------------------------------------------------------------
# Analysis data
#----------------------------------------------------------------------
def analyzeData( conn):
	# Create indexes
	conn.execute( "create index i_files_type on files ( type)")
	conn.execute( "create index i_summary_size on summary ( size)")
	conn.execute( "create index i_summary_levelpath on summary ( level, path)")

	# Analysis
	cur = conn.cursor()

	# 1 - Statistics
	cur.execute( 'select type, count(*) cnt from files group by type');
	rows = cur.fetchall()

	print ""
	print "Statistics:"
	print "-----------"
	for row in rows:
		t = row[0]
		cnt = row[1]

		print "%s: %d" % ( t, cnt)

	# 2 - Total size of directorys
	print ""
	print "Summary directorys, sorted by size:"
	print "----------------------------------------"
	cur.execute( 'select path, size from summary where level <= (select min( level) from summary) order by size desc, path limit 25');
	rows = cur.fetchall()

	for row in rows:
		p = row[0]
		s, t = HumanSize( row[1])

		print "%10.2f %2s: %s" % ( round( s, 2), t, p)

	cur.close()


#----------------------------------------------------------------------
# Main function
#----------------------------------------------------------------------
if __name__ == "__main__":
	if len( sys.argv) != 3:
		print "Syntax: %s analysis.db root-directory" % ( sys.argv[0])
		sys.exit( 1)

	try:
		filename = sys.argv[1]
		rootdir = sys.argv[2]

		if os.path.lexists( filename):
			os.remove( filename)

		conn = sqlite3.connect( filename)
		conn.text_factory = str

	except Exception, e:
		print "Error: %s" % ( e)
		sys.exit( 1)


	# Create tables
	conn.execute( "create table files ( type char(1), path text, filename text, size number, blocks number)")
	conn.execute( "create table summary ( path text, level number, size number, blocks number)")

	# Analyse disk usage
	hasError = False
	try:
		analyzeDir( conn, string.rstrip( rootdir, os.path.sep))
		analyzeData( conn)

	except Exception, e:
		hasError = True
		print "Error: %s" % ( e)

	conn.commit()
	conn.close()

	if hasError:
		sys.exit( 1)
	else:
		sys.exit( 0)

