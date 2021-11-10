import json,os,requests,time



tag_classification_path="tagclassify.txt"
real_path=os.path.split(os.path.realpath(__file__))[0]
img_path=os.path.join(real_path,"Library")
lib_path=os.path.join(real_path,"library.json")
lib_id_path=os.path.join(real_path,"library-id.json")
tag_path=os.path.join(real_path,"tagmap.json")
taglist_path=os.path.join(real_path,"taglist.txt")
tagclassify_path=os.path.join(real_path,"tagclassify.txt")
output_path=os.path.join(real_path,"output")
copy_output_path=os.path.join(output_path,"Copied Pictures")
download_path=os.path.join(img_path,"Downloads")
profile_url="https://www.pixiv.net/ajax/user/%s/profile/all?lang=zh"
usr_url="https://www.pixiv.net/ajax/user/%s?full=0&lang=zh"        
image_url="https://www.pixiv.net/ajax/user/%s/illusts?ids\%5B\%5D=%s&lang=zh" 
artwork_url="https://www.pixiv.net/artworks/"
rank_url="https://www.pixiv.net/ranking.php"

# user proxy (VPN)
# This is the defalt proxy port when you use V2rayN
proxy='127.0.0.1:10809'
proxies={
	'http':'http://'+proxy,
	'https':'http://'+proxy
}

# user cookie , required when download R18 artworks /xyx
cookie= ""

normalheaders = { 
	"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9,accept-encoding: gzip, deflate, br",
	"accept-language": "q=0.9,zh-CN;q=0.8,zh;q=0.7",
	"referer": "https://www.pixiv.net/",
	"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
}
cookieheaders = { 
	"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9,accept-encoding: gzip, deflate, br",
	"accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
	"referer": "https://www.pixiv.net/",
	"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
	"cookie":cookie
}

# Download method Wget , usually in linux
def Wget(url,path,headers):
	cmd="wget "+url+" -c -O \""+path+"\" "
	cmd+="-e http_proxy=http://"+proxy+" "
	cmd+="-e https_proxy=http://"+proxy+" "
	for i in headers.keys():
		cmd+="--header=\""+i+": "+headers[i]+"\" "
	os.system(cmd)
			
# Download method aria2, please put aria2c.exe to system path
def Aria2(url,path,headers):
	print(url,path)
	cmd="aria2c.exe "+url+" -c -d \""+path+"\" ";
	cmd+=" --all-proxy=http://"+proxy+" "
	for i in headers.keys():
		cmd+="--header=\""+i+": "+headers[i]+"\" "
	os.system(cmd)

def ReadJson(path):
	if os.path.exists(path):
		with open(path,"r",encoding="utf-8") as inp:
			temp=inp.read()
			if temp=="":
				return 
			else :
				return json.loads(temp)
	return None

def WriteJson(path,var):
	print(path)
	with open(path,"w",encoding="utf-8") as outp:
		outp.write(json.dumps(var))
imgtype=["png","jpg","gif"]
def Filter(name):
	for i in "\\/:*?\"<>|":
		name=name.replace(i," ")
	return name
def SplitSuffix(filename):
	p=-1
	while True:
		q=filename.find(".",p+1)
		if q==-1: break
		p=q
	if p==-1: return filename,""
	else : return filename[0:p],filename[p+1:]
def DelWhiteSpace(s):
	whitespace=" \t\n\r"
	while len(s):
		if s[0] in whitespace: s=s[1:]
		else: break
	while len(s):
		if s[-1] in whitespace: s=s[:-1]
		else: break
	return s

def CheckTags(tags,keys):
	if type(tags)==list or type(tags)==tuple:
		for i in tags:
			if CheckTags(i,keys):
				return True
		return False
	else :
		return tags in keys

class Library():
	def ReadTagClassification(self):
		if not os.path.exists(tag_classification_path):
			with open(tag_classification_path,"w",encoding="utf-8") as outp:
				pass
		with open(tag_classification_path,"r",encoding="utf-8") as inp:
			s=inp.readlines()
		self.tag_classification={}
		for i in range(0,len(s)):
			p=s[i].find(":{")
			if p==-1: continue
			classification_name=DelWhiteSpace(s[i][0:s[i].find(":{")])
			lis=[]
			for j in range(i+1,len(s)):
				if s[j].find("}")!=-1: break
				temp=DelWhiteSpace(s[j])
				if temp!="": lis.append(temp)
				i=j
			if classification_name in self.tag_classification:
				print("tag_classification error : duplicated classification : "+classification_name)
				exit(0)
			self.tag_classification[classification_name]=lis

	def __init__(self):
		if not os.path.exists(img_path):
			os.makedirs(img_path)
		try: 
			self.lib=ReadJson(lib_path)
			if self.lib==None: self.lib={"ignore":{},"tags":{}}
			if not "ignore" in self.lib: self.lib["ignore"]={}
			if not "tags" in self.lib: self.lib["tags"]={}
			if not os.path.exists(tag_path):
				with open(tag_path,"w",encoding="utf-8"):
					pass
			try: 
				self.tagmap,self.taglist=ReadJson(tag_path)
			except:
				self.tagmap={}
				self.taglist=[]
			self.ReadTagClassification()
			if not os.path.exists(output_path): os.system("mkdir \""+output_path+"\"")
		except Exception as e:
			print(e)
			print("Error when initiating")
			print("Exiting")
			exit(0)
		print("Initiated successfully ,current library state:")
		print("Already ignored "+str(len(self.lib["ignore"].keys()))+" files")
		print("Already got "+str(len(self.lib["tags"].keys()))+" files")
		print("Already got "+str(len(self.taglist))+" tags")
		self.session=requests.Session()
		self.lib_file=open(lib_path,"w",encoding="utf-8")
		self.tag_file=open(tag_path,"w",encoding="utf-8")

	def __del__(self):
		# save when closing...
		print("exiting...")
		self.lib_file.write(json.dumps(self.lib))
		self.tag_file.write(json.dumps([self.tagmap,self.taglist]))
		print("over.")

	def Generate_Tagmap(self):
		self.tagmap={}
		self.taglist=[]
		for i in self.lib["tags"].values():
			for j in i:
				k=j
				if type(j)!=list: k=[j]
				if not k[0] in self.tagmap:
					for l in k: 
						self.tagmap[l]=len(self.taglist)
					self.taglist.append(k)
		
	def SearchForFiles(self,path):
		lis=[]
		def Search(path):
			if os.path.isfile(path):
				lis.append(os.path.split(path))
				return
			for i in os.listdir(path):
				Search(os.path.join(path,i))
		Search(path)
		return lis
			

	def UpdateLibrary(self,redo=False):
		def GetTags(picid):
			while picid.find("_")!=-1:
				picid=picid[:picid.find("_")]
			url=artwork_url+picid
			print(picid,url)
			response=self.session.get(url,proxies=proxies,headers=normalheaders)
			if response.status_code!=200: return "ERROR"
			s=response.text
			l=s.find("\"tags\":{")+7
			r=s.find(",\"alt\":")
			t=s[l:r]
			s=json.loads(t)
			res=[]
			for i in s["tags"]:
				try: res.append((i["tag"],i["translation"]["en"]))
				except: res.append(i["tag"])
			print(res)
			return res

		lis=self.SearchForFiles(img_path)
		for temp in lis:
			if not redo and (temp[1] in self.lib["ignore"] or temp[1] in self.lib["tags"]): continue
			name,typ=SplitSuffix(temp[1])
			print(os.path.join(temp[0],temp[1]),name,typ)
			if typ in imgtype:
				tag=GetTags(temp[1])
				if tag!="ERROR": self.lib["tags"][temp[1]]=tag
				else: self.lib["ignore"][temp[1]]="2"
			else:
				self.lib["ignore"][temp[1]]="1"

		
	def CheckFileExistence(self):
		dic2=self.lib["tags"].copy()
		ExistKey="Existing!#114514"
		lis=self.SearchForFiles(img_path)
		for path,name in lis:
			if name in dic2: dic2[name]=ExistKey
		for i in dic2.keys():
			if dic2[i]!=ExistKey:
				print("Deleted "+i)
				self.lib["tags"].pop(i)

	def CheckDuplicatedFiles(self):
		lis=self.SearchForFiles(img_path)
		dic={}
		for i,j in lis:
			if not j in dic: dic[j]=[]
			dic[j].append(os.path.join(i))
		for i in dic.keys():
			t=dic[i]
			if len(t)==1: continue
			print("Find duplicated file: " + i + " , keep which?")
			for j in range(0,len(t)):
				print("(%d): %s" % (j,t[j]))
			print("-1 to pass these files")
			num=-1
			while True:
				try:
					num=int(input())
					if num<-1 or num>=len(t): 
						print("number out of range")
					else:
						if num==-1: break
						print("Sure?(Y/N/Exit):",end="")
						config=input()
						if config=="Exit": return
						if config=="Y": break
					
				except:
					print("Error input!")
				print("Try Again!")
			if num==-1: continue
			for j in range(0,len(t)):
				if j!=num:
					path=os.path.join(t[j],i)
					print("Delete "+path)
					os.system("del \""+path+"\"")

	def Print_taglist(self):
		taglist=sorted(self.taglist)
		with open(taglist_path,"w",encoding="utf-8") as oup:
			for i in taglist:
				if type(i)==list:
					for j in i:
						oup.write(j+" ")
					oup.write("\n")
				else:
					oup.write(i+"\n")
		print("taglist printed to "+taglist_path)

	def Copy_Pictures_By_Dic(self,img_dic,outputfolder):
		output_path=os.path.join(copy_output_path,outputfolder)
		if not os.path.exists(copy_output_path): os.system("mkdir \""+copy_output_path+"\"")
		if not os.path.exists(output_path): os.system("mkdir \""+output_path+"\"")

		pathlist=[]
		bat_path=os.path.join(real_path,"_run.bat")

		batfile=open("_run.bat","w",encoding="ANSI")
		batfile.write("@echo off\n")
		batfile.write("echo begin copying\n")
		lis=self.SearchForFiles(img_path)
		for temp in lis:
			name,typ=SplitSuffix(temp[1])
			if not typ in imgtype: continue
			if not temp[1] in img_dic: continue
			print("matched file: "+temp[1])	
			path=os.path.join(temp[0],temp[1])
			cmd="copy /Y \""+path+"\" \""+os.path.join(output_path,temp[1])+"\" "
			batfile.write(cmd+"\n")
		batfile.close()
		os.system(bat_path)
		os.system("del "+bat_path)

	def Copy_Pictures_By_TagClassification(self,favorkeys=[],bankeys=[],outputfolder=""):
		favortags={}
		bantags={}
		for key in favorkeys:
			if not key in self.tag_classification: print("key doesn't exist: "+key)
			else : 
				for i in self.tag_classification[key]: favortags[i]=1
		
		for key in bankeys:
			if not key in self.tag_classification: print("key doesn't exist: "+key)
			else : 
				for i in self.tag_classification[key]: bantags[i]=1
		print(favortags)
		img_dic={}
		for i in self.lib["tags"].keys():
			val=self.lib["tags"][i]
			favor=False
			ban=False
			for j in val:
				if type(j)==list:
					for k in j:
						if k in favortags: favor=True
						if k in bantags: ban=True
				else:
					if j in favortags: favor=True
					if j in bantags: ban=True
				if ban: break
			if favor and not ban:
				img_dic[i]=1
		print(img_dic)
		self.Copy_Pictures_By_Dic(img_dic,Filter(outputfolder))

	def Copy_Pictures_By_Tag(self,favortags=[],bantags=[],outputfolder=""):
		img_dic={}
		for i in self.lib["tags"].keys():
			val=self.lib["tags"][i]
			favor=False
			ban=False
			for j in val:
				if type(j)==list:
					for k in j:
						if k in favortags: favor=True
						if k in bantags: ban=True
				else:
					if j in favortags: favor=True
					if j in bantags: ban=True
				if ban: break
			if favor and not ban:
				img_dic[i]=1
		print(img_dic)
		self.Copy_Pictures_By_Dic(img_dic,Filter(outputfolder))

	def Querytag(self,name):
		if name in self.lib["ignore"]: print("file " +name +" ignored")
		else: 
			if name in self.lib["tags"]: 
				print("OK file exists")
				print(self.lib["tags"][name])
			else:
				 print("Find no existence of "+name)
	def QueryFilepath(self,name):
		lis=self.SearchForFiles(img_path)
		for i in lis:
			if i[1]==name:
				print(os.path.join(i[0],i[1]))
	def DeleteFile(self,name):
		lis=self.SearchForFiles(img_path)
		for i in lis:
			if i[1]==name:
				path=os.path.join(i[0],i[1])
				print("Find file at "+path)
				print("Deleted?(Y/N)")
				config=input()
				if config=="Y":
					os.system("del \""+path+"\"")
					print(path+" deleted")
		print("OK")

	def Get_Illust_Info(self,illust_id):
		url=artwork_url+illust_id
		print(url)
		s=self.session.get(url,proxies=proxies,headers=normalheaders).text

		l=s.find("\"tags\":{")+7
		r=s.find(",\"alt\":")
		t=s[l:r]
		tmp=json.loads(t)
		res=[]
		for i in tmp["tags"]:
			try: res.append((i["tag"],i["translation"]["en"]))
			except: res.append(i["tag"])

		p=s.find("\""+illust_id+"\":{\"id\":\""+illust_id+"\"")
		p=s.find("\"pageCount\"",p+1)
		p=s.find(":",p+1)
		q=s.find(",",p+1)
		count=int(s[p+1:q])
		
		p=s.find("\"original\"")
		p=s.find(":",p+1)
		p=s.find("\"",p+1)
		q=s.find("\"",p+1)
		picurl=s[p+1:q]
		p=0
		while True:
			q=picurl.find(".",p+1)
			if q==-1: break
			p=q
		filetype=picurl[p+1:]
		p=0
		while True:
			q=picurl.find("/",p+1)
			if q==-1: break
			p=q
		picurl=picurl[:p+1]
		return (count,picurl,filetype,res)

	def Download_By_Id(self,illust_id,download_path="",ignore=True,bankeys=[]):
		if type(illust_id)!=str:
			try: 
				illust_id=str(illust_id)
			except:
				print("Type Error , illust id should be string or integer")
				return


		count,picurl,filetype,tags=self.Get_Illust_Info(illust_id)
		if CheckTags(tags,bankeys): 
			print("Illust banned")
			return

		print("Downloading ",illust_id,"page count=",count,"filetype=",filetype)
		if not os.path.exists(download_path): os.system("mkdir \""+download_path+"\"")
		if count>4:
			download_path=os.path.join(download_path,illust_id)
			if not os.path.exists(download_path): os.system("mkdir \""+download_path+"\"")
		for i in range(0,count):
			path=illust_id+"_p"+str(i)+"."+filetype
			if ignore and (path in self.lib["tags"] or path in self.lib["ignore"]): 
				print("Omitted " + path)
				continue
			url=picurl+path
			print("url=",url)
			print(path,tags)
			Aria2(url,download_path,normalheaders)
			self.lib["tags"][path]=tags

	def Get_User_Illusts(self,userid):
		url=profile_url%userid
		print(url)
		f=self.session.get(url,proxies=proxies,headers=cookieheaders)
		print(f.status_code)
		if f.status_code!=200:
			print("Error Get user illusts")
			return []
		f=f.content
		print("Get User !")
		g=json.loads(f)["body"]
		return list(g["illusts"].keys())

	def Download_By_User(self,userid,bankeys=[]):
		illust_list=self.Get_User_Illusts(userid)
		path=os.path.join(download_path,str(userid))
		cnt=0
		for picid in illust_list: 
			cnt+=1
			print("Downloading %d of %d " % (cnt,len(illust_list)))
			self.Download_By_Id(picid,path,bankeys=bankeys)
		self.UpdateLibrary()

	def Download_RankTop(self,num):
		resp=self.session.get(rank_url,proxies=proxies,headers=normalheaders)
		if resp.status_code!=200:
			print("error")
			return
		s=resp.text
		p=0
		num=min(num,100)
		for i in range(0,num):
			p=s.find("href=\"/artworks",p+1)+16
			q=s.find("\"",p+1)
			print("Downloading %d of %d " % (i+1,num) )
			self.Download_By_Id(s[p:q],os.path.join(download_path,"rank"))

	def Download_Missing_File(self):
		dic1=self.lib["ignore"].copy()
		dic2=self.lib["tags"].copy()
		ExistKey="Existing!#114514"
		lis=self.SearchForFiles(img_path)
		for path,name in lis:
			if name in dic1: dic1[name]=ExistKey
			if name in dic2: dic2[name]=ExistKey
		for i in dic2.keys():
			if dic2[i]!=ExistKey:
				print("Found missing file: "+i)
				j=i[:i.find("_")]
				print(j)
				self.Download_By_Id(j,os.path.join(download_path,"temp"),ignore=False)

	def Update_Ignore_By_MissingFile(self):
		dic=self.lib["tags"].copy()
		ExistKey="Existing!#114514"
		lis=self.SearchForFiles(img_path)
		for path,name in lis:
			if name in dic: dic[name]=ExistKey
		for i in dic.keys():
			if dic[i]!=ExistKey:
				print("Ignored "+i)
				self.lib["ignore"][i]="3";
	def Copy_All(self,path):
		lis=self.SearchForFiles(img_path)
		dic={}
		for i in lis:
			a,b=i[0],i[1]
			if b in self.lib["tags"]:
				dic[b]=1
		self.Copy_Pictures_By_Dic(dic,path)


if __name__=='__main__':
	lib=Library()
	# Command examples 
	''' Library command
	lib.UpdateLibrary() # search library and do tagging, 
	lib.UpdateLibrary(redo=True) # redo tagging of all artworks
	# 'missing' means this file is in library.json ,but not found in /Library folder
	lib.Download_Missing_File()
	lib.CheckFileExistence() # delete information of missing files.
	lib.Update_Ignore_By_MissingFile() 
	# add all missing files to ban list, which is useful when you deleted some pictures.

	lib.Generate_Tagmap()
	lib.Print_taglist() # These two commands are used together to print tags to taglist.txt
	'''

	''' Command on single file
	lib.Querytag("64627054_p0.jpg")
	lib.QueryFilepath("64627054_p0.jpg")
	lib.DeleteFile("88096577_p0.png")
	'''

	'''Copy Command
	lib.Copy_Pictures_By_TagClassification(favorkeys=["初音ミク"],bankeys=["R-18"],outputfolder="初音ミク")
	lib.Copy_Pictures_By_Tag(favortags=["白发"],bantags=[],outputfolder="白发")
	lib.Copy_All(path="All")
	'''

	''' Download Command
	lis=[] # pixiv user id
	for i in lis:
		lib.Download_By_User(i,bankeys=['腐向け'])


	lis=[] # pixiv artwork id, which does not contain 'p_0.png'
	for i in lis:
		lib.Download_By_Id(i,os.path.join(download_path,"temp")) 
		lib.Download_By_Id(i,os.path.join(download_path,"temp"),ignore=False)  # this command will not ignore files already in the library.

	lib.Download_RankTop(20) # Download top 20 files.
	'''
	lib.Download_RankTop(20)


