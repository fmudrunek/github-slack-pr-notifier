import fetch
import send

def main():
	print("STARTING!")
	fetch.run("/config.json")
	send.run()
	



if __name__== "__main__":
  main()