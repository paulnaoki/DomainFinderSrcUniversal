from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer
from DomainFinderSrc.MiniServer.Common.AbstractServer import abstract_main
from .CentralProcessing import CentralProcessingUnit


def main(HOST=MiningTCPServer.DefaultListenAddr, PORT=MiningTCPServer.DefaultListenPort):
    handler = CentralProcessingUnit()
    abstract_main(handler, HOST=HOST, PORT=PORT)

if __name__ == "__main__":
    main()