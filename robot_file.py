#!/usr/bin/env python

import pandas as pd
import numpy as np
import random
import re
import argparse


def seed_prob(high_seed):
    """

    Win probability by historical seed matchup (first round matchups only)

    """
    
    df_seed = pd.read_csv('seed_winning_history.csv', names=['matchup','win_pct'])
    return df_seed[df_seed['matchup'].str.startswith(str(high_seed)+' vs.')]['win_pct'].values[0]




def determine_winner(team1,team2,firstround=False):
    """

    Randomly determines the winner between two teams based on their BPI.
    Two teams are a row from BPI data frame
    
    """
    
    team1_bpi = team1.BPI.values
    team2_bpi = team2.BPI.values
    
    total_bpi = team1_bpi + team2_bpi

    # probability of team1 winning
    team1_prob = team1_bpi / total_bpi
    
    #modify probability of winning first round by historical seed matchup probability
    #probably should add a check for existence of seed
    if (firstround):
        if (team1.seed == 1):
            return team1
        team1_prob = (team1_prob + seed_prob(team1.seed))/2. #need to make sure minimum seed is team1

    if random.random() < team1_prob:
        return team1
    else:
        return team2


def get_bpi():
    df_bpi = pd.read_csv('BPI_24_25_final.csv')
    df_bpi['TEAM'] = df_bpi['TEAM'].map(lambda x: x.lstrip('\n'))
    return df_bpi


def predict_regional_winner(bracket, verbose=False):
  """
  Predicts the winner of a region.

  Args:
    bracket: A list representing the tournament bracket.
             The bracket is structured as a list of matchups.
             Each matchup is a tuple of two teams.
    verbose: True = print winners of each matchup in each round

  """

  if not bracket:
    return None  # Empty bracket

  df_bpi = get_bpi()

  current_round = [(df_bpi[df_bpi.TEAM.str.startswith(matchup[0])], df_bpi[df_bpi.TEAM.str.startswith(matchup[1])]) for matchup in bracket]

  myround = 1
  while len(current_round) >= 1:
    if verbose: print (f'\n round {myround} winners') 
    next_round = []
    for matchup in current_round:
      winner = determine_winner(matchup[0], matchup[1])
      if verbose: print (winner.TEAM.values) 
      next_round.append(winner)

    # Reshape the next round into pairs for the next set of matches
    if len(next_round) > 1:
      reshaped_next_round = []
      for i in range(0, len(next_round), 2):
        reshaped_next_round.append((next_round[i], next_round[i+1]))

      current_round = reshaped_next_round
      myround += 1
    else:
      current_round=next_round
      break


  # The remaining team is the Final Four
  return next_round[0]


def get_bracket(region):
    #read in bracket
    with open(region+'bracket.txt', 'r') as file:
        content = file.read()

    seeding = re.split('\n', content)
    seeding = [s.rstrip() for s in seeding]
    seeding = [re.sub(r'^\d+', '', s).strip() for s in seeding]

    #disambiguation, LOL
    seeding = [re.sub(r'Michigan$', 'Michigan Wolverines', s).strip() for s in seeding]
    seeding = [re.sub(r'Alabama$', 'Alabama Crimson', s).strip() for s in seeding]
    seeding = [re.sub(r'Illinois$', 'Illinois Fighting', s).strip() for s in seeding]
    seeding = [re.sub(r'Texas$', 'Texas Longhorns', s).strip() for s in seeding]
   

    matchups = list(zip(seeding[::2], seeding[1::2]))
    return matchups


def get_final_four(verbose = False):
    final_four = {}
    regions = ['south','west','east','midwest']
    for reg in regions:
        if (verbose): print (f'\n Region {reg}') 
        bracket = get_bracket(reg)
        final_four[reg]=predict_regional_winner(bracket, verbose=verbose)
    return final_four

def champ(verbose = False):

    final4 = get_final_four(verbose = verbose)
    semi1 = determine_winner(final4['south'],final4['west'])
    semi2 = determine_winner(final4['midwest'],final4['east'])
    champ = determine_winner(semi1,semi2)

    if (verbose): 
        print(f' The championship game will be played between {semi1.TEAM.values[0]} and {semi2.TEAM.values[0]}')
        print(f'{champ.TEAM.values[0]} will win overall')
    return champ.TEAM.values[0]


def prob_final_four(n=10000):
    """
    
    run final_four n times to get probability of final_fours
    
    """
    
    mprob4 = {}
    for i in range(0,n):
        my4 = get_final_four(verbose = False)
        for team in my4.values():
            key = team.TEAM.values[0]
            if key in mprob4:
                mprob4[key] += 1
            else:
                mprob4[key] = 1
    
    sorted_mprob = dict(sorted(mprob4.items(), key=lambda item: item[1], reverse=True))
    # TBD fix to pretty print dict
    print(f'Out of {n} brackets the teams reached the final four in this many: {sorted_mprob}')
    
    return

def prob_champ(n=10000):
    """
    
    run champ n times to get probability of winning it all
    
    """
    mprob_champ= {}
    for i in range(0,n):
        key = champ(verbose = False)
        if key in mprob_champ:
            mprob_champ[key] += 1
        else:
            mprob_champ[key] = 1
    
    sorted_mprob = dict(sorted(mprob_champ.items(), key=lambda item: item[1], reverse=True))

    # TBD fix to pretty print dict
    print(f'Out of {n} brackets the teams won in this many times: {sorted_mprob}')
    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="generate tourney results")
    parser.add_argument("--verbose", action="store_true", help="print one bracket")
    parser.add_argument("--final4", action="store_true", help="final four probability")
    parser.add_argument("--champ", action="store_true", help="champ probability")

    args = parser.parse_args()

    if args.verbose:
        champ(verbose = True)

    elif args.final4:
        prob_final_four(n=10000)
    
    elif args.champ:
        prob_champ(n=10000)

    else:
        print("Usage: python robot_file.py --verbose --final4 --champ (choose one argument option)")



