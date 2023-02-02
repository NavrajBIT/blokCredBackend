//SPDX-License-Identifier: MIT

pragma solidity 0.8.14;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
// import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";

contract certificate is ERC721URIStorage{
    uint256 public tokenCounter;

    uint256 public ownerCount;
    mapping(address => uint256) public ownerToOwnerId;
    uint256 public blockedOwnerCount;
    mapping(address => uint256) public blockedOwnerToOwnerId;

    constructor(string memory _name, string memory _symbol)
        ERC721(_name, _symbol)
    {
        tokenCounter = 0;

        blockedOwnerCount = 0;
        ownerCount = 1;
        ownerToOwnerId[msg.sender] = ownerCount;
    }

    modifier onlyOwner() {
        require(
            ownerToOwnerId[msg.sender] > 0,
            "Only owner can call this function."
        );
        require(
            blockedOwnerToOwnerId[msg.sender] == 0,
            "You have been blocked."
        );
        _;
    }

    function setOwner(address _newOwner) public onlyOwner {
        require(ownerToOwnerId[_newOwner] == 0, "Owner already added.");
        ownerCount = ownerCount + 1;
        ownerToOwnerId[_newOwner] = ownerCount;
    }

    function blockOwner(address _owner) external onlyOwner {
        require(msg.sender != _owner, "You cannot block yourself");
        blockedOwnerCount = blockedOwnerCount + 1;
        blockedOwnerToOwnerId[_owner] = blockedOwnerCount;
    }

    function createCertificate(string memory _tokenURI, address _receiver)
        public
        onlyOwner
        returns (uint256 newTokenId)
    {
        tokenCounter = tokenCounter + 1;
        _safeMint(msg.sender, tokenCounter);
        _setTokenURI(tokenCounter, _tokenURI);
        transferFrom(msg.sender, _receiver, tokenCounter);
        // _tokenIdByOwner[_receiver] = tokenCounter;
        // tokenBySender[msg.sender][_receiver] = tokenCounter;
        return tokenCounter;
    }

    function updateCertMetadata(uint256 _tokenId, string memory _newTokenURI)
        public
    {
        require(_tokenId > 0 && _tokenId <= tokenCounter);
        // require(msg.sender == ownerOf(_tokenId));
        _setTokenURI(_tokenId, _newTokenURI);
    }

    // mapping(address => uint256) public _tokenIdByOwner;
    // mapping(address => mapping(address => uint256)) public tokenBySender;

    // function ownerOfTokens(address _userAddress) public view returns (uint256) {
    //     uint256 tokenID = _tokenIdByOwner[_userAddress];
    //     return tokenID;
    // }

    // function tokenBysenderAdd(address _from, address _reciever)
    //     public
    //     view
    //     returns (uint256)
    // {
    //     uint256 tokenID = tokenBySender[_from][_reciever];
    //     return tokenID;
    // }

    
    // function createCertificate(string memory _tokenURI)
    //     public
    //     onlyOwner
    //     returns (uint256 newTokenId)
    // {
    //     tokenCounter = tokenCounter + 1;
    //     _safeMint(msg.sender, tokenCounter);
    //     _setTokenURI(tokenCounter, _tokenURI);
    //     return tokenCounter;
    // }
}
