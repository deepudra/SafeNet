pragma solidity ^0.8.0;

contract SafeNet {
    struct Threat {
        string url;
        bytes32 codeHash;
        address reporter;
        string reporterName;
        address[] verifiers;
        bool isBlacklisted;
    }

    string[] public allUrlList; 
    mapping(string => Threat) public threats;
    mapping(address => uint256) public balances;
    mapping(address => mapping(string => bool)) public hasVerified;

    function reportThreat(string memory _url, bytes32 _codeHash, string memory _name) public {
        if (threats[_url].reporter == address(0)) {
            allUrlList.push(_url);
            threats[_url].url = _url;
            threats[_url].codeHash = _codeHash;
            threats[_url].reporter = msg.sender;
            threats[_url].reporterName = _name;
            threats[_url].isBlacklisted = false;
        }
    }

    function verifyThreat(string memory _url) public {
        Threat storage t = threats[_url];
        require(t.reporter != address(0), "Not reported");
        require(msg.sender != t.reporter, "Reporter cannot verify");
        require(!hasVerified[msg.sender][_url], "Already verified");

        t.verifiers.push(msg.sender);
        hasVerified[msg.sender][_url] = true;

        if (t.verifiers.length >= 2) {
            t.isBlacklisted = true;
            balances[t.reporter] += 10;
            balances[msg.sender] += 2;
        }
    }

    function getVerifiers(string memory _url) public view returns (address[] memory) {
        return threats[_url].verifiers;
    }

    function getAllUrls() public view returns (string[] memory) {
        return allUrlList;
    }
}