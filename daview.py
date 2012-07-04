#----------------------------------------------------------------------
# Show file and directory information of disk analyszer database
#----------------------------------------------------------------------
import sys
import os
import os.path
import sqlite3


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
# show directory
#----------------------------------------------------------------------
def showDirectory( conn, directory = ""):
	cur = conn.cursor()

	# 1 - Statistics
	if len( directory) == 0:
		cur.execute( 'select type, count(*) cnt from files group by type')
	else:
		cur.execute( "select type, count(*) cnt from files where (path = '%s' or path like '%s%s%%') group by type" % ( directory, directory, os.path.sep))
	rows = cur.fetchall()

	print ""
	print "Statistics:"
	print "-----------"
	for row in rows:
		t = row[0]
		cnt = row[1]

		print "%s: %d" % ( t, cnt)

	# 2 - Total size of directorys
	if len( directory) == 0:
		print ""
		print "Summary top directorys, sorted by size:"
		print "---------------------------------------"
		cur.execute( 'select path, size from summary where level <= (select min( level) + 1 from summary) order by size desc')
	else:
		print ""
		print "Summary directorys, sorted by size (first 20):"
		print "----------------------------------------------"
		cur.execute( "select path, size from summary where (path = '%s' or path like '%s%s%%') order by size desc limit 20" % ( directory, directory, os.path.sep))

	rows = cur.fetchall()

	for row in rows:
		p = row[0]
		s, t = HumanSize( row[1])

		print "%10.2f %2s: %s" % ( round( s, 2), t, p)

	cur.close()


#----------------------------------------------------------------------
# show files
#----------------------------------------------------------------------
def showFiles( conn, directory):
	cur = conn.cursor()

	print ""
	print "File of %s" % ( directory)
	print "--------------------------------------------------"
	cur.execute( "select type, filename, size from files where path = '%s' and type = 'F' order by size desc" % (directory))

	rows = cur.fetchall()

	for row in rows:
		p = row[1]
		s, t = HumanSize( row[2])

		print "%10.2f %2s: %s" % ( round( s, 2), t, p)

	cur.close()


#----------------------------------------------------------------------
# show files
#----------------------------------------------------------------------
def searchFiles( conn, findname):
	cur = conn.cursor()

	print ""
	print "Search file or directory"
	print "------------------------"
	cur.execute( "select type, path, filename, size from files where (upper( path) like upper( '%%%s%%') or upper( path) like upper( '%%%s%%')) and type = 'F' order by size desc limit 20" % (findname, findname))

	rows = cur.fetchall()

	for row in rows:
		p = "%s%s%s" % (row[1], os.path.sep, row[2])
		s, t = HumanSize( row[3])

		print "%10.2f %2s: %s" % ( round( s, 2), t, p)

	cur.close()


#----------------------------------------------------------------------
# Main function
#----------------------------------------------------------------------
if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "Syntax: %s diskanalyse.db" % ( sys.argv[0])
		sys.exit( 1)

	try:
		filename = sys.argv[1]
		conn = sqlite3.connect( filename)
		conn.text_factory = str

		input = sys.stdin
		output = sys.stdout

		output.write( "\n")
		output.write( "Welcome to disk analyse view\n")
		output.write( "connected to database %s\n" % ( filename))
		showDirectory( conn)
		output.write( "\n> ")

		while 1:
			line = input.readline().strip()
			parts = line.split()

			if len( parts) > 0:
				if parts[0].strip() == "help" or parts[0].strip() == "h" or parts[0].strip() == "?":
					output.write( "\n")
					output.write( "(d)irectory [directory] => show directory\n")
					output.write( "(f)iles directory => show files\n")
					output.write( "(s)earch what => search file or directory by name\n")
					output.write( "(h)elp => show this help\n")
					output.write( "(e)xit => exit from this shell\n")
					output.write( "\n")

				elif parts[0].strip() == "exit" or parts[0].strip() == "e":
					break

				elif parts[0].strip() == "quit" or parts[0].strip() == "q":
					break

				elif parts[0].strip() == "directory" or parts[0].strip() == "d":
					# Analyse disk usage
					if len( parts) > 1:
						showDirectory( conn, parts[1])
					else:
						showDirectory( conn)

				elif parts[0].strip() == "files" or parts[0].strip() == "f":
					if len( parts) > 1:
						showFiles( conn, parts[1])
					else:
						output.write( "No directory defined.\n")
						output.write( "Syntax: files directory\n")

				elif parts[0].strip() == "search" or parts[0].strip() == "s":
					if len( parts) > 1:
						searchFiles( conn, parts[1])
					else:
						output.write( "No search term defined.\n")
						output.write( "Syntax: search search-term\n")

				else:
					output.write( "Unknown command\n")

			output.write( "\n> ")

		conn.close()
		sys.exit( 0)

	except KeyboardInterrupt:
		conn.close()
		sys.exit(1)

	except Exception, e:
		conn.close()
		print "Error: %s" % ( e)
		sys.exit( 1)

