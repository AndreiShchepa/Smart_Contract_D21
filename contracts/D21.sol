// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import "./IVoteD21.sol";

contract D21 is IVoteD21 {
    address public owner;
    mapping(address => Subject) public subjects;
    address[] public subjectAddresses;
    mapping(address => bool) public voters;
    bool public votingStarted;
    uint256 public votingEndTime;
    
    // To track how many votes a voter has cast (2 positive and 1 negative)
    struct VoterVotes {
        uint8 positiveVotes;
        bool negativeVoteUsed;
    }
    mapping(address => VoterVotes) public voterVoteCount;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    modifier onlyVoter() {
        require(voters[msg.sender], "Not an eligible voter");
        _;
    }

    modifier votingActive() {
        require(votingStarted, "Voting has not started");
        require(block.timestamp <= votingEndTime, "Voting has ended");
        _;
    }

    modifier votingNotActive() {
        require(!votingStarted, "Voting is active, cannot perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function addSubject(string memory name) external override votingNotActive {
        require(subjects[msg.sender].votes == 0, "Subject already registered");

        subjects[msg.sender] = Subject(name, 0);
        subjectAddresses.push(msg.sender);
    }

    function addVoter(address addr) external override onlyOwner {
        voters[addr] = true;
    }

    function getSubjects() external view override returns (address[] memory) {
        return subjectAddresses;
    }

    function getSubject(address addr) external view override returns (Subject memory) {
        return subjects[addr];
    }

    function startVoting() external override onlyOwner votingNotActive {
        require(subjectAddresses.length > 0, "No subjects registered");
        votingStarted = true;
        votingEndTime = block.timestamp + 2 days;
    }

    function votePositive(address addr) external override onlyVoter votingActive {
        require(voterVoteCount[msg.sender].positiveVotes < 2, "Already cast two positive votes");
        require(subjects[addr].votes != 0, "Subject not found");

        subjects[addr].votes += 1;
        voterVoteCount[msg.sender].positiveVotes += 1;

        // Insert sorting optimization
        _sortSubjectAfterVote(addr);
    }

    function voteNegative(address addr) external override onlyVoter votingActive {
        require(voterVoteCount[msg.sender].positiveVotes >= 2, "Need 2 positive votes first");
        require(!voterVoteCount[msg.sender].negativeVoteUsed, "Already used negative vote");
        require(subjects[addr].votes != 0, "Subject not found");

        subjects[addr].votes -= 1;
        voterVoteCount[msg.sender].negativeVoteUsed = true;

        // Insert sorting optimization
        _sortSubjectAfterVote(addr);
    }

    function getRemainingTime() external view override returns (uint256) {
        if (block.timestamp > votingEndTime) {
            return 0;
        }
        return votingEndTime - block.timestamp;
    }

    // Gas-efficient sorting: Insert sorting happens only when votes are cast
    function _sortSubjectAfterVote(address addr) internal {
        int256 currentVotes = subjects[addr].votes;

        uint256 length = subjectAddresses.length;
        for (uint256 i = 0; i < length - 1; i++) {
            if (subjectAddresses[i] == addr) {
                for (uint256 j = i; j < length - 1; j++) {
                    if (subjects[subjectAddresses[j + 1]].votes < currentVotes) {
                        subjectAddresses[j] = subjectAddresses[j + 1];
                    } else {
                        break;
                    }
                }
                subjectAddresses[length - 1] = addr;
                break;
            }
        }
    }

    function getResults() external view override returns (Subject[] memory) {
        uint256 length = subjectAddresses.length;
        Subject[] memory sortedSubjects = new Subject[](length);

        // No need to sort as they are pre-sorted during voting
        for (uint256 i = 0; i < length; i++) {
            sortedSubjects[i] = subjects[subjectAddresses[i]];
        }
        return sortedSubjects;
    }
}