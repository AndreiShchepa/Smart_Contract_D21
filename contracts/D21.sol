// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import "./IVoteD21.sol";

contract D21 is IVoteD21 {
    mapping(string => bool) private registeredNames;
    mapping(address => Subject) public subjects;
    mapping(address => bool) public voters;
    address[] public subjectAddresses;
    uint256 public votingEndTime;
    bool public votingStarted;
    address public owner;
    
    struct VoterVotes {
        uint8 positiveVotes;
        bool negativeVoteUsed;
        mapping(address => bool) votedSubjects;
    }

    mapping(address => VoterVotes) private voterVoteCount;
    mapping(address => bool) private isSubject;


    ////////////// MODIFIERS //////////////
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
    ///////////////////////////////////////


    constructor() {
        owner = msg.sender;
    }


    ////////////// HELP FUNCTIONS //////////////
    function hasVoterVotedForSubject(address voter, address subject) external view returns (bool) {
        return voterVoteCount[voter].votedSubjects[subject];
    }

    function votePositiveInternal(address subject_) private {
        require(voterVoteCount[msg.sender].positiveVotes < 3, "Already cast three positive votes");
        require(bytes(subjects[subject_].name).length > 0, "Subject not found");
        require(!voterVoteCount[msg.sender].votedSubjects[subject_], "Already voted for this subject");

        subjects[subject_].votes += 1;
        voterVoteCount[msg.sender].positiveVotes += 1;
        voterVoteCount[msg.sender].votedSubjects[subject_] = true;

        _sortSubjectAfterVote(subject_);
        emit PositiveVoted(msg.sender, subject_);
    }

    function voteNegativeInternal(address subject_) private {
        require(voterVoteCount[msg.sender].positiveVotes >= 2, "Need 2 positive votes first");
        require(!voterVoteCount[msg.sender].negativeVoteUsed, "Already used negative vote");
        require(bytes(subjects[subject_].name).length > 0, "Subject not found");
        require(!voterVoteCount[msg.sender].votedSubjects[subject_], "Already voted for this subject");

        subjects[subject_].votes -= 1;
        voterVoteCount[msg.sender].negativeVoteUsed = true;
        voterVoteCount[msg.sender].votedSubjects[subject_] = true;

        _sortSubjectAfterVote(subject_);
        emit NegativeVoted(msg.sender, subject_);
    }
    ////////////////////////////////////////////


    ////////////// MAIN FUNCTIONS //////////////
    function addSubject(string memory name) external override votingNotActive {
        require(!isSubject[msg.sender], "Address already registered as a subject");
        require(bytes(name).length > 0, "Empty name can not be registered");
        require(!registeredNames[name], "Subject name already exists");

        isSubject[msg.sender] = true;
        registeredNames[name] = true;
        subjectAddresses.push(msg.sender);
        subjects[msg.sender] = Subject(name, 0);
        
        emit SubjectAdded(msg.sender, name);
    }

    function addVoter(address voter_) external override onlyOwner {
        voters[voter_] = true;
        emit VoterAdded(voter_);
    }

    function getSubjects() external view override returns (address[] memory) {
        return subjectAddresses;
    }

    function getSubject(address addr_) external view override returns (Subject memory) {
        return subjects[addr_];
    }

    function startVoting() external override onlyOwner votingNotActive {
        require(subjectAddresses.length > 0, "No subjects registered");
        votingStarted = true;
        votingEndTime = block.timestamp + 4 days;
        emit VotingStarted();
    }

    function votePositive(address subject_) public override onlyVoter votingActive {
        require(voterVoteCount[msg.sender].positiveVotes < 3, "Already cast three positive votes");
        require(bytes(subjects[subject_].name).length > 0, "Subject not found");
        require(!voterVoteCount[msg.sender].votedSubjects[subject_], "Already voted for this subject");

        subjects[subject_].votes += 1;
        voterVoteCount[msg.sender].positiveVotes += 1;
        voterVoteCount[msg.sender].votedSubjects[subject_] = true;

        _sortSubjectAfterVote(subject_);
        emit PositiveVoted(msg.sender, subject_);
    }

    function voteNegative(address subject_) public override onlyVoter votingActive {
        require(voterVoteCount[msg.sender].positiveVotes >= 2, "Need 2 positive votes first");
        require(!voterVoteCount[msg.sender].negativeVoteUsed, "Already used negative vote");
        require(bytes(subjects[subject_].name).length > 0, "Subject not found");
        require(!voterVoteCount[msg.sender].votedSubjects[subject_], "Already voted for this subject");

        subjects[subject_].votes -= 1;
        voterVoteCount[msg.sender].negativeVoteUsed = true;
        voterVoteCount[msg.sender].votedSubjects[subject_] = true;

        _sortSubjectAfterVote(subject_);
        emit NegativeVoted(msg.sender, subject_);
    }    

    function voteBatch(address[] calldata subjects_, bool[] calldata votes_) external override onlyVoter votingActive {
        require(subjects_.length == votes_.length, "Arrays length mismatch");
        require(subjects_.length > 0, "Empty arrays not allowed");
        
        for (uint256 i = 0; i < subjects_.length; i++) {
            if (votes_[i]) {
                votePositiveInternal(subjects_[i]);
            } else {
                voteNegativeInternal(subjects_[i]);
            }
        }
    }

    function getRemainingTime() external view override returns (uint256) {
        if (block.timestamp > votingEndTime) {
            return 0;
        }
        
        return votingEndTime - block.timestamp;
    }

    /**
     * Maintains sorted order of subjects during voting to optimize getResults
     * - Reduces gas cost by spreading sorting across vote transactions
     * - Avoids expensive sorting operation when retrieving results
     * - Only moves the voted subject to its correct position
     */
    function _sortSubjectAfterVote(address addr) private {
        int256 votesToSort = subjects[addr].votes;
        uint256 length = subjectAddresses.length;
        uint256 currentIndex;

        // Find current position
        for (currentIndex = 0; currentIndex < length; currentIndex++) {
            if (subjectAddresses[currentIndex] == addr) {
                break;
            }
        }

        // Sort upwards if votes increased
        if (currentIndex > 0 && votesToSort > subjects[subjectAddresses[currentIndex - 1]].votes) {
            uint256 targetIndex = currentIndex;
            while (targetIndex > 0 && subjects[subjectAddresses[targetIndex - 1]].votes < votesToSort) {
                address temp = subjectAddresses[targetIndex];
                subjectAddresses[targetIndex] = subjectAddresses[targetIndex - 1];
                subjectAddresses[targetIndex - 1] = temp;
                targetIndex--;
            }
        }
        // Sort downwards if votes decreased
        else if (currentIndex < length - 1 && votesToSort < subjects[subjectAddresses[currentIndex + 1]].votes) {
            uint256 targetIndex = currentIndex;
            while (targetIndex < length - 1 && subjects[subjectAddresses[targetIndex + 1]].votes > votesToSort) {
                address temp = subjectAddresses[targetIndex];
                subjectAddresses[targetIndex] = subjectAddresses[targetIndex + 1];
                subjectAddresses[targetIndex + 1] = temp;
                targetIndex++;
            }
        }
    }

    /**
     * @notice Get voting results in descending order by votes
     * @dev Gas-optimized through several mechanisms:
     * 1. Array is kept sorted during voting via _sortSubjectAfterVote
     * 2. No sorting needed at retrieval time, just a single pass copy
     * 3. Minimal memory operations - just one array allocation
     * 4. View function - no state modifications, lower gas cost
     */
    function getResults() external view override returns (Subject[] memory) {
        require(block.timestamp > votingEndTime, "Voting hasn't ended yet");
        
        uint256 length = subjectAddresses.length;
        Subject[] memory sortedSubjects = new Subject[](length);

        // Single pass copy of pre-sorted array
        for (uint256 i = 0; i < length; i++) {
            sortedSubjects[i] = subjects[subjectAddresses[i]];
        }
        
        return sortedSubjects;
    }
    ////////////////////////////////////////////
}