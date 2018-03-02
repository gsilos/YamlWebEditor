# Yaml Web Editor 

So, why I wrote this program? 

Yaml files are said to be easy of READING by humans. Maybe true :-). But certainly this is not true when I see human WRITING it. Yaml files are made for computers and humans to read it. The problem lives when a computer needs to read a yaml file that was manually written by humans.

By observing how people handle yaml files, most of the time, I found that lot of then WROTE bad yaml files, disrespecting yaml's specification (http://yaml.org/spec/1.1/) when using normal editors like vim or notepad++. This is really bad because Yaml files change the behaviour of Applications and when you need to send a manually edited yaml configuration file to production environment this can break things and put the company into trouble in certain situations.

Okay, some of you may say that these people could install a magic plugin to try to make things easier, even using online yaml validators. I tried as hard as I can to not to write this code by googling, trying to find something already made in the community, but in the end I found that this code is the only thing that fits the scenario in the company I work for at this moment.

So to make this conversation short here, this software is fruit of these observations and is my contribution to try to help my coleagues edit yaml configuration files easily and by consequence of this, make safe deployments in production or any other environment. From now on the guys who are responsible for feeding the yaml file can just focus in the business and keep the rest for computers.

Now you can see that the YamlWebEditor is not only an editor, it can be used collaboratively among team's members inside Slack (for example) to enrich content of yaml configuration file along time and when the yaml reach its final version it can be used with Jenkins pipeline to be deployed to an environment.

If you want to see these integrations working in practice, send me an email and I can show it to you by the price of less than 10 minutes of your time ;^)

# Features

- restrict edit/show functions for sensitive data (HiddenFields: some keys like password cant be viewed/edited by all users)
- retrieve yaml files using either ssh or md5hash keys (this is the magic for jenkins and slackbot integrations)

# Run Docker Demo

```
$ git clone https://github.com/gsilos/YamlWebEditor.git
$ cd YamlWebEditor
$ docker build -t ywe .
$ docker run -i -p 8421:8421 -t ywe
```
open your browser @ http://dockerip:8421

# TODO

- Local database authentication
- AD authentication
- classify users (only admin role can edit/see HiddenFields values)
- remove keys from yaml

This release it only support editing yaml  files whose values contains string, int, float and boolean. This is enough for my scenario. Feel free to change it for your needs ;-). This Dockerfile is used only for demo. If you want to run this program, you need to adjust the "basket" folder for persistence.

