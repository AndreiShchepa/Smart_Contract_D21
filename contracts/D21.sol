// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import "./IVoteD21.sol";

// voter cann ot be subject
// subject can not be voter

contract D21 is IVoteD21 {
    address public owner;
    mapping(string => bool) private registeredNames;
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
        require(subjects[msg.sender].votes == 0 && bytes(subjects[msg.sender].name).length == 0, "Address already registered as a subject");
        require(!registeredNames[name], "Subject name already exists");
        require(bytes(name).length > 0, "Empty name can not be registered");

        registeredNames[name] = true;
        subjectAddresses.push(msg.sender);
        subjects[msg.sender] = Subject(name, 0);
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
        require(bytes(subjects[addr].name).length > 0, "Subject not found");

        subjects[addr].votes += 1;
        voterVoteCount[msg.sender].positiveVotes += 1;

        // Insert sorting optimization
        _sortSubjectAfterVote(addr);
    }

    function voteNegative(address addr) external override onlyVoter votingActive {
        require(voterVoteCount[msg.sender].positiveVotes >= 2, "Need 2 positive votes first");
        require(!voterVoteCount[msg.sender].negativeVoteUsed, "Already used negative vote");
        require(bytes(subjects[addr].name).length > 0, "Subject not found");

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
        uint256 currentIndex;

        // Find the current index of the voted subject
        for (currentIndex = 0; currentIndex < length; currentIndex++) {
            if (subjectAddresses[currentIndex] == addr) {
                break;
            }
        }

        // Move the subject up in the list if its votes have increased
        while (currentIndex > 0 && subjects[subjectAddresses[currentIndex - 1]].votes < currentVotes) {
            subjectAddresses[currentIndex] = subjectAddresses[currentIndex - 1];
            currentIndex--;
        }

        // Move the subject down in the list if its votes have decreased
        while (currentIndex < length - 1 && subjects[subjectAddresses[currentIndex + 1]].votes > currentVotes) {
            subjectAddresses[currentIndex] = subjectAddresses[currentIndex + 1];
            currentIndex++;
        }

        // Place the subject at its correct position
        subjectAddresses[currentIndex] = addr;
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