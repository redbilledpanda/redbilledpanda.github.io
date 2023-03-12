#!/usr/bin/env python3

"""
update_tags.py
Script to automatically create tags posts for a Jekyll blog hosted
in Github pages. First, it fishes all tags. Then, it creates the
tags posts. Lastly, it adds the generated files, commits them, and pushes 
them to the corresponding repository. Preferably run this script
when having a clean working space (nothing to commit/push).
Based on Long Qian's post
https://longqian.me/2017/02/09/github-jekyll-tag/

Originally written by:
@author: Arturo Moncada-Torres 
https://github.com/arturomoncadatorres/arturomoncadatorres.github.io

arturomoncadatorres@gmail.com
"""

#%% Preliminaries.
import glob
import os

import git
import pdb
import pathlib
import itertools
import sys

#%% Define paths.
post_dir = '_posts/'
tag_dir = 'tag/'


#%%
def get_tags(post_dir=post_dir, verbose=True):
    '''
    Adapted from tag_generator.py
    Copyright 2017 Long Qian
    Contact: lqian8@jhu.edu
    This script created tags for a Jekyll blog hosted by Github page.
    No plugins required.
    See https://longqian.me/2017/02/09/github-jekyll-tag/
    
    Updated 2019-12-05
    Arturo Moncada-Torres
    arturomoncadatorres@gmail.com
    Adapted script to process .md files with tags in format
    tags:
        - tag1
        - tag2
        ...
    Notice that for this to work properly, tags must be the last element of the
    Markdown header.
    
    Parameters
    ----------
    post_dir: string
        Path to directory _posts/
        
    verbose: boolean
        Indicate if status messages are printed (True) or not (False)


    Returns
    -------
    total_tags: set
        Set with all the tags used in the different posts.
    '''    
   
    # Get Markdown posts files.
    PathList = pathlib.Path(os.getcwd()).rglob('*.md')
    PathList1 = pathlib.Path(os.getcwd()).rglob('*.markdown')
    
    
    # Loop through all files.
    total_tags = []
    for path in itertools.chain(PathList, PathList1):
        if path.is_file():
            if '~' in path.suffix:
                pdb.set_trace()
                continue
            with open(path.absolute(), 'r', encoding='utf8') as f:
                crawl = False
                tag_lines_coming = False
                for line in f:
                    current_line = line.strip()
                    if crawl:
                        if current_line == 'tags:':
                            tag_lines_coming = True
                            continue
                        
                    # If --- delimiter is found, start crawling.
                    if current_line == '---':
                        if not crawl:
                            crawl = True
                        else:
                            crawl = False
                            break
                        
                    # If we are in the actual tag lines (that is, tag_lines_coming is
                    # True and we aren't in the tags: line), extract them.
                    if tag_lines_coming and (current_line != 'tags:'):
                        total_tags.append(current_line.strip('- '))
        else:
            continue
        
    # Make tags unique in a set.
    total_tags = set(total_tags)
    
    if verbose:
        print("Found " + str(total_tags.__len__()) + " tags")
    
    return total_tags


#%%
def create_tags_posts(tag_dir=tag_dir, total_tags=set(), verbose=True):
    '''
    Adapted from tag_generator.py
    Copyright 2017 Long Qian
    Contact: lqian8@jhu.edu
    This script created tag posts for a Jekyll blog hosted by Github page.
    No plugins required.
    See https://longqian.me/2017/02/09/github-jekyll-tag/
    
    Updated 2019-12-11
    Arturo Moncada-Torres
    arturomoncadatorres@gmail.com
    Modularized for ease of use in update_tags.py.
    
    Parameters
    ----------
    post_dir: string
        Path to directory directory where tag posts will be created.
        
    total_tags: set
        
        
    verbose: boolean
        Indicate if status messages are printed (True) or not (False)


    Returns
    -------
    None
    '''
    
    if total_tags.__len__() == 0:
        print("No tags. Thus, no tag posts were created")
        return None
    
    else:
    
        old_tags = glob.glob(tag_dir + '*.md')
        for tag in old_tags:
            os.remove(tag)
            
        if not os.path.exists(tag_dir):
            os.makedirs(tag_dir)
        
        for tag in total_tags:
            tag_filename = tag_dir + tag + '.md'
            f = open(tag_filename, 'a')
            write_str = '---\nlayout: tag_page\ntitle: \"Tag: ' + tag + '\"\ntag: ' + tag + '\nrobots: noindex\n---\n'
            f.write(write_str)
            f.close()
            
        if verbose:
            print("Created " + str(total_tags.__len__()) + " tag posts")
            
        return None


#%%
if __name__ == '__main__':
    try:
        commitMsg = sys.argv[1]
        commitEmail = sys.argv[2]        
    except IndexError as e:
        print(f"usage:\n{sys.argv[0]} commitMsg(enclosed in quotes) commitEmail ")
        print(e)
        sys.exit(1)        

    pdb.set_trace()
    tags = get_tags(os.getcwd())
    create_tags_posts(tag_dir, tags)

    # For Git.
    repo = git.Repo(os.getcwd())

    # Add files for commit.
    try:
        repo.git.add(tag_dir)
    except:
        print("Error ocurred while adding files to Git.")

    # Commit changes.    
    try:
        repo.git.commit('-m', str(commitMsg), author=commitEmail)
    except Exception as e:
        print("Error occurred while commiting.")
        print(e)
    
    # Push commit.
    try:
        origin = repo.remote(name='origin')
        origin.push()
    except Exception as e:
        print("Error occurred while pushing.")
        print(e)
