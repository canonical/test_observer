# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.



from test_observer.external_apis.issue_tracking.url_parser import IssueURLParser


class TestIssueURLParser:
    """Test suite for IssueURLParser"""
    
    def test_parse_github_url(self):
        """Test parsing GitHub issue URLs"""
        url = "https://github.com/canonical/test-observer/issues/123"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.platform == "github"
        assert result.host == "github.com"
        assert result.external_id == "123"
        assert result.owner == "canonical"
        assert result.repo == "test-observer"
        assert result.project is None
    
    def test_parse_github_url_with_http(self):
        """Test parsing GitHub issue URLs with HTTP scheme"""
        url = "http://github.com/canonical/test-observer/issues/456"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.platform == "github"
        assert result.external_id == "456"
    
    def test_parse_jira_url_canonical(self):
        """Test parsing canonical Jira URLs"""
        url = "https://warthogs.atlassian.net/browse/TEST-123"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.platform == "jira"
        assert result.host == "warthogs.atlassian.net"
        assert result.external_id == "TEST-123"
        assert result.project == "TEST"
        assert result.owner is None
        assert result.repo is None
    
    def test_parse_jira_url_different_host(self):
        """Test parsing Jira URLs from different hosts"""
        url = "https://company.atlassian.net/browse/PROJ-456"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.platform == "jira"
        assert result.host == "company.atlassian.net"
        assert result.external_id == "PROJ-456"
        assert result.project == "PROJ"
    
    def test_parse_launchpad_url(self):
        """Test parsing Launchpad bug URLs"""
        url = "https://bugs.launchpad.net/ubuntu/+bug/123456"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.platform == "launchpad"
        assert result.host == "bugs.launchpad.net"
        assert result.external_id == "123456"
        assert result.owner is None
        assert result.repo is None
        assert result.project is None
    
    def test_parse_launchpad_url_different_project(self):
        """Test parsing Launchpad bug URLs for different projects"""
        url = "https://bugs.launchpad.net/snapd/+bug/789012"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.platform == "launchpad"
        assert result.external_id == "789012"
    
    def test_parse_unsupported_url(self):
        """Test parsing unsupported URLs returns None"""
        unsupported_urls = [
            "https://example.com/issues/123",
            "https://bitbucket.org/user/repo/issues/123",
            "https://gitlab.com/user/repo/-/issues/123",
            "https://redmine.example.com/issues/123",
        ]
        
        for url in unsupported_urls:
            result = IssueURLParser.parse_url(url)
            assert result is None, f"Expected None for unsupported URL: {url}"
    
    def test_parse_invalid_url(self):
        """Test parsing invalid URLs returns None"""
        invalid_urls = [
            "",
            "not-a-url",
            "https://github.com",  # Missing issue number
            "https://github.com/user",  # Missing repo and issue
            "https://github.com/user/repo",  # Missing issue number
            "https://bugs.launchpad.net/project",  # Missing bug number
            "https://warthogs.atlassian.net/browse",  # Missing issue key
        ]
        
        for url in invalid_urls:
            result = IssueURLParser.parse_url(url)
            assert result is None, f"Expected None for invalid URL: {url}"
    
    def test_parse_github_url_with_extra_path(self):
        """Test parsing GitHub URLs with extra paths are ignored"""
        url = "https://github.com/canonical/test-observer/issues/123/comments"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.external_id == "123"
    
    def test_parse_jira_url_with_extra_params(self):
        """Test parsing Jira URLs with query parameters"""
        url = "https://warthogs.atlassian.net/browse/TEST-123?focusedCommentId=12345"
        result = IssueURLParser.parse_url(url)
        
        assert result is not None
        assert result.external_id == "TEST-123"
    
    def test_is_supported_url(self):
        """Test is_supported_url method"""
        supported_urls = [
            "https://github.com/canonical/test-observer/issues/123",
            "https://warthogs.atlassian.net/browse/TEST-123",
            "https://bugs.launchpad.net/ubuntu/+bug/123456",
        ]
        
        unsupported_urls = [
            "https://example.com/issues/123",
            "https://bitbucket.org/user/repo/issues/123",
            "",
            "not-a-url",
        ]
        
        for url in supported_urls:
            assert IssueURLParser.is_supported_url(url), f"Expected supported: {url}"
            
        for url in unsupported_urls:
            assert not IssueURLParser.is_supported_url(url), f"Expected unsupported: {url}"
    
    def test_parse_url_edge_cases(self):
        """Test edge cases in URL parsing"""
        # Test case sensitivity
        url = "https://GITHUB.com/User/Repo/issues/123"
        result = IssueURLParser.parse_url(url)
        assert result is None  # Should be None because hostname doesn't match exactly
        
        # Test with port numbers
        url = "https://company.atlassian.net:8080/browse/TEST-123"
        result = IssueURLParser.parse_url(url)
        assert result is not None
        assert result.host == "company.atlassian.net:8080"