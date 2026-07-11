from config import ConfigLoader

from services.retroarch import CoreResolver



config = ConfigLoader().load()



resolver = CoreResolver(

    config

)



core = resolver.find(

    "genesis_plus_gx"

)



print(core)
