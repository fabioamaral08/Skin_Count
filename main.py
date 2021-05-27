from lcu_driver import Connector
from tkinter import messagebox
import psutil
import pandas as pd
import Sheets_API as sheets
from tqdm import tqdm

"""
####################################
Check if LOL is OPEN
####################################
"""
connector = Connector()
def process_exists():
    for p in psutil.process_iter():
        try:
            if p.name() == 'LeagueClient.exe':
                return True
        except psutil.Error:
            return False


##################################################################
#Get info from client
def on_startup():
    @connector.ready
    async def connect(connection):
        summoner = await connection.request('get', '/lol-summoner/v1/current-summoner')
        if summoner.status == 200:
            data = await summoner.json()
            summoner = str(data['summonerId'])
            summoner_name = str(data['displayName'])
            
            universe = await connection.request('get','/lol-game-data/assets/v1/universes.json')
            universe = await universe.json()

            champion_get = await connection.request('get','/lol-champions/v1/inventories/' + summoner + '/champions')
            champion_data = await champion_get.json()


            ## GET OWNED CHAMPIONS
            owned_champs = list()
            champ_name = dict()
            for c in champion_data:
                champ_name[str(c['id'])] = c['name']
                if c['ownership']['owned']:
                    owned_champs.append(c['id'])

            ## GET SKIN SET NAMES
            skin_set_get = await connection.request('get','/lol-game-data/assets/v1/skinlines.json')
            skin_set_data = await skin_set_get.json()
            skin_set_data = skin_set_data[1:]

            skinLine_name = dict()
            for skinLine in skin_set_data:
                skinLine_name[str(skinLine['id'])] = skinLine['name']
            

            universe = await connection.request('get','/lol-game-data/assets/v1/universes.json')
            universe = await universe.json()
            universe = universe[1:]
            universe_name = dict()
            for uni in universe:
                universe_name[str(uni['id'])] = uni['name']
            universe_name

            """
            #######################################################
            #######             SKINLINES                   #######
            #######################################################
            """
            ##GET OWNED SKIN
            skin_set = sheets.get_from_sheets('Skinlines')
            new_index = list(skinLine_name.keys())
            if skin_set is None or len(skin_set.index) < len(new_index):
                skin_set = pd.DataFrame({
                    'Set': skinLine_name.values(),
                    summoner_name:'NOT_OWNED'
                })
            elif summoner_name not in skin_set.columns:
                skin_set[summoner_name] = 'NOT_OWNED'
            skin_set.index = new_index
            owned_skins = list()

            #Skin line by champion
            champ_sets = dict()
            for i in skinLine_name.keys():
                champ_sets[i] = set()

            for c_id in tqdm(owned_champs, desc='Counting skins by Skinlines'):
                skin_get = await connection.request('get', '/lol-champions/v1/inventories/' + summoner + f'/champions/{c_id}/skins')
                skin_get = await skin_get.json()

                champ_data = await connection.request('get',f'/lol-game-data/assets/v1/champions/{c_id}.json')
                champ_data = await champ_data.json()
                skin_data = champ_data['skins']
                for skin in skin_get:
                    if not skin['isBase'] and skin['ownership']['owned']:
                        s_id = skin['id']
                        owned_skins.append(s_id)
                        for s in skin_data:
                            if s['id'] == s_id:
                                if s['skinLines'] is not None:
                                    sl_id = str(s['skinLines'][0]['id'])
                                    skin_set.loc[sl_id][summoner_name]='OWNED'
                                    (champ_sets[sl_id]).add(champ_name[str(c_id)])
                                    break
                
            ## GET FRAGMENT LOOT INFO
            loot = await connection.request("get", '/lol-loot/v1/player-loot')
            loot = await loot.json()

            for l in tqdm(loot,desc='Counting Fragments by Skinlines'):
                if l['displayCategories'] == 'SKIN' and l['itemStatus'] == "NONE":
                    champ_id = l['parentStoreItemId']
                    s_id = l['storeItemId']
                    champ_data = await connection.request('get',f'/lol-game-data/assets/v1/champions/{champ_id}.json')
                    champ_data = await champ_data.json()
                    skin_data = champ_data['skins']
                    for s in skin_data:
                        if s['id'] == s_id:
                            if s['skinLines'] is not None:
                                sl_id = str(s['skinLines'][0]['id'])
                                (champ_sets[sl_id]).add(f'FRAG_{champ_name[str(champ_id)]}')
                                if skin_set.loc[sl_id][summoner_name] == 'NOT_OWNED':
                                    skin_set.loc[sl_id][summoner_name]='Frag'
                                break
                            

            df_summoner = pd.DataFrame()

            for cs in champ_sets.keys():
                c_list = list(champ_sets[cs])
                c = ','.join([i for i in c_list])
                df = pd.DataFrame({'Champions':[c]})
                df_summoner = df_summoner.append(df)
            df_summoner = df_summoner["Champions"].str.split(',', expand=True)
            df_summoner.fillna('',inplace=True)
            df_summoner['Skinline'] = list(skinLine_name.values())
            df_summoner = df_summoner[[df_summoner.columns[-1]]+ list(df_summoner.columns[:-1])]
            sheets.update_sheets(df_summoner,f'{summoner_name}_Skinlines')
            sheets.update_sheets(skin_set,'Skinlines')

            """
            #######################################################
            #######             UNIVERSE                   #######
            #######################################################
            """


            ##GET OWNED SKIN
            universe_set = sheets.get_from_sheets('Universes')
            new_index = list(universe_name.keys())
            if universe_set is None or len(universe_set.index) < len(new_index):
                universe_set = pd.DataFrame({
                    'Set': universe_name.values(),
                    summoner_name:'NOT_OWNED'
                })
            elif summoner_name not in universe_set.columns:
                universe_set[summoner_name] = 'NOT_OWNED'
            universe_set.index = new_index

            #Universe by champion
            champ_sets = dict()
            for i in universe_name.keys():
                champ_sets[i] = set()


            for c_id in tqdm(owned_champs, desc='Counting Skins by Universe'):
                skin_get = await connection.request('get', '/lol-champions/v1/inventories/' + summoner + f'/champions/{c_id}/skins')
                skin_get = await skin_get.json()

                champ_data = await connection.request('get',f'/lol-game-data/assets/v1/champions/{c_id}.json')
                champ_data = await champ_data.json()
                skin_data = champ_data['skins']
                for skin in skin_get:
                    if not skin['isBase'] and skin['ownership']['owned']:
                        s_id = skin['id']
                        for s in skin_data:
                            if s['id'] == s_id:
                                if s['skinLines'] is not None:
                                    sl_id = s['skinLines'][0]['id']
                                    for u in universe:
                                        if sl_id in u['skinSets']:
                                            universe_set.loc[str(u['id'])][summoner_name]='OWNED'
                                            (champ_sets[str(u['id'])]).add(champ_name[str(c_id)])
                                            break
                                    break
                
            ## GET FRAGMENT LOOT INFO
            loot = await connection.request("get", '/lol-loot/v1/player-loot')
            loot = await loot.json()

            for l in tqdm(loot, desc='Counting Fragments by Universe'):
                if l['displayCategories'] == 'SKIN' and l['itemStatus'] == "NONE":
                    champ_id = l['parentStoreItemId']
                    s_id = l['storeItemId']
                    champ_data = await connection.request('get',f'/lol-game-data/assets/v1/champions/{champ_id}.json')
                    champ_data = await champ_data.json()
                    skin_data = champ_data['skins']
                    for s in skin_data:
                        if s['id'] == s_id:
                            if s['skinLines'] is not None:
                                sl_id = s['skinLines'][0]['id']
                                for u in universe:
                                    if sl_id in u['skinSets']:
                                        (champ_sets[str(u['id'])]).add(champ_name[str(champ_id)])
                                        if universe_set.loc[str(u['id'])][summoner_name]=='NOT_OWNED':
                                            universe_set.loc[str(u['id'])][summoner_name]='Frag'
                                        break
                                
            df_summoner = pd.DataFrame()
            for cs in champ_sets.keys():
                c_list = list(champ_sets[cs])
                c = ','.join([i for i in c_list])
                df = pd.DataFrame({'Champions':[c]})
                df_summoner = df_summoner.append(df)
            df_summoner = df_summoner["Champions"].str.split(',', expand=True)
            df_summoner.fillna('',inplace=True)
            df_summoner['Universe'] = list(universe_name.values())
            df_summoner = df_summoner[[df_summoner.columns[-1]]+ list(df_summoner.columns[:-1])]
            sheets.update_sheets(df_summoner,f'{summoner_name}_Universe')
            sheets.update_sheets(universe_set,'Universes')
        else:
            messagebox.showerror("ERROR", "YOU MUST TO BE LOGGED IN")
            # messagebox.showerror("ERROR", "THERE WAS AN ERROR")
            exit(1)
    @connector.close
    async def disconnect(connection):
        print('Finished task')
        await connector.stop()
    
    connector.start()

if __name__ == '__main__':

    if process_exists():
        print('Counting Skins and Fragments...')
        on_startup()
    else:
        messagebox.showerror("ERROR", "LEAGUE CLIENT IS NOT OPEN")