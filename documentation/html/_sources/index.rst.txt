.. _top:

.. contents::

Introduction
============
GLOM is a tool that helps you organize your language, and generate glossed example sentences. It can read dictionary files (i.e. words and their translations) as well as tables (inflections, case markings, pronouns paradigms, etc.), and also supports sound change rules. The name GLOM stands for 'GLOsses and MOrphemes', but also alludes to that fact that you can 'stick things together' with it. It was created for people making their own languages, who have control over their morphology, but could plausible be used with natural languages if you structured your data the right way.

`Return to top <#top>`_


Getting GLOM
============
Download the zip file from GitHub <https://github.com/ReadingGlosses/GLOM>here</a>. Unzip it somewhere on your computer than you can remember later.

`Return to top <#top>`_


Running GLOM
============

When you download GLOM, it comes with language files for a mini-lang called "Tirilian", so that you can immediately run it and see how it works, before you commit any time into setting up your own files. For some flavour, Tirilian is a language spoken by a fictitious human society, who live in a rigid legalistic culture. Only members of the Law Society are allowed to learn and use this language. 

GLOM uses a simple command line interface (CLI). To run GLOM with the included Tirilian files, you need open the Command Prompt (Windows) or Terminal (Mac) and run the following::


   cd C:\Users\ReadingGlosses\GLOM
   glom.py --input_file tiril_sentences.txt --output_file glossed_tiril_sentence.txt


Change the folder to match the one on your computer, but leave the file names as they are.

If you get an error says that 'glom.py' isn't recognized, trying  type '.\glom.py' instead (this seems to be necessary in Windows Powershell).

There is a full description of the CLI here, although most people will only ever need the ``--input_file`` and ``--output_file`` arguments.

`Return to top <#top>`_

Setting Up GLOM
===============

Conceptually, there are a few different types of files that are used with GLOM. They're all just plain text files though, so nothing complex is required. Each of these is explained in their own section below, and there are example files that are downloaded with GLOM.
 
#. An input file that tells GLOM which morphemes you want to glue together.
#. Dictionary files, which are lists of morphemes paired with glosses. These are useful for root words, affixes, and grammatical particles. 
#. Paradigm files, which are tables of morphemes, organized by category. These are useful for representing information like verb conjugations, case endings, or independent pronoun sets.
#. Sound change file (optional). GLOM can apply phonological rules to your words, after combining the morphemes together. You will be able to see words both before and after any changes take place. 

`Return to top <#top>`_

The Input File
--------------

The input file is a plain text file, where each line consists of an natural language translation (I'm using English) and then a sequence of glosses from your language. The included Tirilian input file looks like this::


   a witness testified  witness-NOM.SG.ANIM LAW-testify-ORALEV-PAST.1.ANIM.UNWRIT
   the officer made an error in ruling   officer.of.the.court-NOM.HON.ANIM UNLAW-make.ruling-COMPL
   the judge is reading a scroll   judge-JHON-NOM.HON.ANIM LAW-read-INCL scroll-ACC.SG.INAN


You can separate the values with a tab, as I did here, or with a comma. If you'd prefer things in the other order, with glosses first, then run GLOM with the argument ``--input_order gloss``

`Return to top <#top>`_

Glossing Conventions
--------------------

* Use spaces to separate words, use hyphens to separate morphemes within words.
* Use lower-case letters for lexical items, like 'witness' or 'scroll'.
* Use upper-case letters or digits for grammatical categories, like '1' for 'first person' or 'NOM' for 'nominative case'. 
* If you need more than one word to gloss a lexical item, separate each word by a period, like 'officer.of.the.court' or 'make.ruling'
* If a morpheme represents more than one grammatical category, separate them by either a period, like NOM.HON.ANIM

`Return to top <#top>`_

Dictionary Files
----------------

In the context of GLOM, a dictionary is a plain text file where each line contains a morpheme in your language along with its gloss, separated by a comma or tab. These files should only include basic roots or affixes which cannot be decomposed into any smaller parts ("mono-morphemic lexical items").

The Trilian example has three files: roots.txt, with some basic nouns and verbs, evidentials.txt for a list of evidentials (obviously), and affixes.txt which is other stuff that I didn't feel like categorizing more finely. You are free to divide up the information in whatever way makes sense to you, or just to use a huge unabbriged.txt file. You can modify your files at any point, so you aren't locked into a particular categorization.

roots.txt::

   law,sxat
   judge,jaxt
   witness,taw
   scroll,ite
   officer.of.the.court,pan
   make.ruling,ta
   testify,sut
   read,hal 

evidentials.txt::

   LITEV,fulu,information obtained from a written source
   ORALEV,tulu,information obtained by talking to someone
   PRECEV,unut,used for citing legal precedent

affixes.txt::

   HON,ti,honorific added to many legal title
   JHON,te,honorific added for judges specifically
   LAW,-ife,action done in accordance with the law
   UNLAW,-sip,action done illegally
   INCL,et-,incomplete, not started, hypothetical
   COMPL,exe-,complete, factual

The default formatting for dictionary files is to have the gloss first, then the morpheme in your language. If you prefer the reverse order, with the morpheme first, then run GLOM with the option ``--dictionary_order morpheme``. Dictionary files can be tab or comma separated (as long as you are consistent within a file).

GLOM also ignores everything after the second column, so you can write any additional notes that you want in there. Just like the input file, you can separate things by tabs instead of commas if you prefer, just be consistent across your files.

`Return to top <#top>`_

Affix types
^^^^^^^^^^^

You can specify the affix type in the dictionary file using hyphens (or by adding a comment). This is optional, but can be useful for keeping track of your language. GLOM doesn't need this information because you've already supplied the correct order of morphemes in your input to the program. 

Prefixes and suffixes are straightforward to implement, as shown above. 

Circumfixes can be treated as independent morphemes, and you can list them both in a dictionary file. For example, Tirillian has 'criminal instrumental' (CRIM) case marked by a circumfix a- -um. The dictionary file can be updated as follows::

   CRIM1,a-,implies a noun was used to commit a crime, first part of a circumfix
   CRIM2,-um,second part of the above circumfix
   art,wijax

Which can be used to create this glossed example::

   awijaxum
   a-wijax-um
   CRIM1-art-CRIM2
   'forgery'

Unfortunately, infixes are not supported directly through GLOM. Infixation rules are often context-sensitive and require extra linguistic analysis, e.g. "insert after the first vowel" means you have to figure out what a 'vowel' is, and this might not be consistent across orthographies.

`Return to top <#top>`_

Paradigm Files
--------------

A paradigm file is a chart or table, which is useful when your morphemes combine more than one meaning or category. Tirilian nouns are marked for nominative and accusative, and these paradigms are in a file called 'case_endings.txt' in the paradigms folder. This file contains one table for nominative::

   NOM,ANIM,INAN
   SG,e,i,x
   PL,ut,uti,xu
   HON,tep,tapi,@

And another for accusative::

   ACC,ANIM,INAN
   SG,u,a,s
   PL,al,uli,su
   HON,sep,sapi,@

The first entry in each table must be the gloss for the paradigm. I chose NOM for nominative case and ACC for accusative case. The rest of table is interpreted as expected. The rows represent singular, plural, and honorific forms, while the columns represent animate and inanimate distinctions. The @ symbol means no morpheme is present. As elsewhere, you use commas or tabs, just be consistent within each file. You can put more than one table into a single file, but there has to be at least one blank line between them!

To refer to a particular element in this table, you write the gloss as name.row.column. For example, if I need the accusative plural animate, I write the gloss ACC.PL.ANIM. If you'd prefer to read the tables columns first (so, ACC.ANIM.PL) then run GLOM with the argument --table_order column. (Just make sure you're consistent!)

After the tables, you can include an option "notes" section with information about the paradigm. This section must start with the "#" symbol. As soon as GLOM sees this, it stops reading the file, so you can't include additional paradigms after your notes. There's a notes section in the case_endings.txt file that you can check for yourself.

`Return to top <#top>`_

Multi-dimensional tables
^^^^^^^^^^^^^^^^^^^^^^^^

If you have a particularly complex morphology, a 2-dimensional table might not be enough.  Tirilian verbs encodes 3 dimensions of information in the past tense: grammatical number of the subject (1,2,3,honorific), grammatical gender of the subject (animate, inanimate), and whether the event is recorded somewhere in a law journal (written, unwritten/unsure if written). 

This is too much information to fit into a table, but it can be represented in columns like this::

   PAST,1,ANIM,WRIT,x
   PAST,1,ANIM,UNWRIT,s
   PAST,1,INAM,WRIT,al
   PAST,1,INAM,UNWRIT,el
   PAST,2,ANIM,WRIT,xi
   PAST,2,ANIM,UNWRIT,si
   PAST,2,INAM,WRIT,il
   PAST,2,INAM,UNWRIT,ul
   PAST,3,ANIM,WRIT,xo
   PAST,3,ANIM,UNWRIT,so
   PAST,3,INAM,WRIT,ol
   PAST,3,INAM,UNWRIT,olo
   PAST,HON,ANIM,WRIT,atl
   PAST,HON,ANIM,UNWRIT,etl
   PAST,HON,INAM,WRIT,@
   PAST,HON,INAM,UNWRIT,@

You can access these glosses the same as as with tables. For example, the firsrt person animinate unwritten past 's' is glossed as PAST.1.ANIM.UNWRIT 

`Return to top <#top>`_

Sound Change File (Optional)
----------------------------

You can optionally add sound changes for your language. Each line of the sound change file must contain a phonological rule using a format like this::

   x -> h / _[-back,+voc,-cons]
   p -> x / #_
   t -> s / _t
   @ -> j / [-cons,+voc]_[-cons,+voc]

The changes will be applied after GLOM has constructed words. Rules apply sequentially, in order. This can have an effect on the outcome. In this example, /x/ becomes /h/ before front vowel, and /p/ becomes /x/ at the beginning of words. Since they apply in this order, a word like /piti/ will always be pronounced as /xiti/. If the order of the rules were revered, then /piti/ would become /hiti/

Sound changes are implemented using a version of my Ursus rule engine. For information about how to author the rules, please read `this documentation <https://readingglosses.com/user-guide-writing-phonological-rules/>`_. You can also experiment with Ursus using `this web interface <https://phonology-readingglosses.pythonanywhere.com/>`_, if you just want to play around with your phonology for a while.

Output File
===========

After processing your input, GLOM will produce a new file of glossed example sentences. The format of the output is as follows:

* Line 1: Transcription
* Line 2: Morpheme breakdown
* Line 3: Gloss
* Line 4: Translation

If you ran GLOM with a sound change file, the change are applied to the transcription on line 1. The morpheme breakdown shows the 'underlying forms' before any rules. If you didn't use a sound change file, then the transcription will look the same as the morpheme breakdown, except it won't have any hyphens.

Here's part of the output from the example Tirilian files::

   tawe ihesutustulu
   taw-e               ixe-sut-ut-tulu          
   witness-NOM.SG.ANIM LAW-testify-COMPL-ORALEV 
   a witness testified

The gloss and translation are exactly as in the input file, but the morphemes have been added, and left-aligned with words. Sound changes are also applied to the transcription: the /x/ in the LAW prefix becomes /h/ between vowels, and the /tt/ sequences at the boundary between the COMPL and ORALENV suffixes becomes /st/

`Return to top <#top>`_

