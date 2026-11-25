package com.softserve.teachua.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.modelmapper.ModelMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import jakarta.servlet.Filter;
import jakarta.servlet.RequestDispatcher;
import jakarta.servlet.http.HttpServletRequest;

import java.util.Set;

@Configuration
public class ApplicationConfig {

    private static final Set<String> TEST_STATUS_PATHS = Set.of("/200", "/400", "/409", "/500");

    @Value("${server.servlet.context-path}")
    private String rootUri;

    @Bean
    public FilterRegistrationBean customFilterBean() {
        FilterRegistrationBean<Filter> filterFilterRegistrationBean = new FilterRegistrationBean<>();
        filterFilterRegistrationBean.setFilter((request, response, chain) -> {
            HttpServletRequest req = (HttpServletRequest) request;
            String requestUri = req.getRequestURI();
            if (!requestUri.startsWith(rootUri + "/static/") &&
                    !requestUri.startsWith(rootUri + "/api/") &&
                    !requestUri.startsWith(rootUri + "/actuator") &&
                    !TEST_STATUS_PATHS.contains(requestUri.substring(rootUri.length())) &&
                    !requestUri.equals(rootUri + "/")) {
                RequestDispatcher requestDispatcher = request.getRequestDispatcher( "/");
                requestDispatcher.forward(request, response);
                return;
                }

            chain.doFilter(request, response);
        });
        return filterFilterRegistrationBean;
    }

    @Bean
    public ModelMapper modelMapper() {
        return new ModelMapper();
    }

//    @Bean
//    public PasswordEncoder passwordEncoder() {
//        return new BCryptPasswordEncoder();
//    }

    @Bean
    public ObjectMapper objectMapper() { return new ObjectMapper(); }
}
