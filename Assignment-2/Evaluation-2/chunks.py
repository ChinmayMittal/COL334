import random
import hashlib

def get_hash(s):
    return hashlib.md5(s.encode()).hexdigest()

def get_chunk(id):
    
    chunks = {
        1:'The young man wanted a role model. He looked long and hard in his youth, but that role model never materialized. His only choice was to embrace all the people in his life he didnt want to be like.',
        2: 'She considered the birds to be her friends. Shed put out food for them each morning and then shed watch as they came to the feeders to gorge themselves for the day. She wondered what they would do if something ever happened to her.',
        3: 'There was a time when he would have embraced the change that was coming. In his youth, he sought adventure and the unknown, but that had been years ago. He wished he could go back and learn to find the excitement that came with change but it was useless.',
        4: 'She tried not to judge him. His ratty clothes and unkempt hair made him look homeless. Was he really the next Einstein as she had been told? On the off chance it was true, she continued to try not to judge him.',
        5: 'It was going to rain. The weather forecast didnt say that, but the steel plate in his hip did. He had learned over the years to trust his hip over the weatherman. It was going to rain, so he better get outside and prepare.',
        6: 'The headphones were on. They had been utilized on purpose. She could hear her mom yelling in the background, but couldnt make out exactly what the yelling was about',
        7: 'That was exactly why she had put them on. She knew her mom would enter her room at any minute, and she could pretend that she hadnt heard any of the previous yelling.',
        8: 'MaryLou wore the tiara with pride. There was something that made doing anything she didnt really want to do a bit easier when she wore it. She really didnt care what those staring through the window were thinking as she vacuumed her apartment.',
        9: 'He couldnt move. His head throbbed and spun. He couldnt decide if it was the flu or the drinking last night. It was probably a combination of both.',
        10: 'I recently discovered I could make fudge with just chocolate chips, sweetened condensed milk, vanilla extract, and a thick pot on slow heat.'
    }
    
    chunk = chunks[id]
    md5 = get_hash(chunk)
    pCorrupt = random.choice([1,2,3])
    if(pCorrupt == 1):
        chunk = f'{random.random()} this string has been corrupted. please request it again.'
    return chunk, md5


    
    
